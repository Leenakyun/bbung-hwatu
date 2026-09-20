from .rules.bbung import can_declare_bbung
from .rules.bomb import calculate_hand_score
from datetime import datetime, timedelta, timezone
from .rules.stop import (
    StopType,
    calculate_stop_score,
    get_available_stops,
)
from .state import (
    BagajiDeclaration,
    BombBagajiDeclaration,
    GameState,
    GameStatus,
    RoundEndReason,
    TurnPhase,
)
from .rules.bagaji import (
    can_declare_bomb_bagaji,
    can_declare_general_bagaji,
    get_bomb_months_for_bagaji,
)
from .rules.surprise_stop import (
    calculate_two_card_sum,
    can_declare_surprise_stop,
    has_surprise_stop_dokbak,
)
from .deck import Deck
from .setup import deal_initial_cards
from .models import (
    AIDifficulty,
    Card,
    PlayerType,
)
from .ai.beginner import (
    choose_beginner_bbung_cards,
    choose_beginner_discard,
    choose_beginner_general_bagaji_month,
    choose_beginner_bomb_bagaji_month,
)
from .ai.intermediate import (
    choose_intermediate_discard,
)
from .ai.advanced import (
    choose_advanced_discard,
    choose_advanced_stop,
    choose_advanced_bbung_cards,
    choose_advanced_general_bagaji_month,
    choose_advanced_bomb_bagaji_month,
    should_advanced_declare_surprise_stop,
)
from .ai.tazza import (
    choose_tazza_discard,
    choose_tazza_stop,
    choose_tazza_bbung_cards,
    choose_tazza_general_bagaji_month,
    choose_tazza_bomb_bagaji_month,
    should_tazza_declare_surprise_stop,
)



class GameEngine:
    """
    게임 상태를 실제로 변경하는 중앙 엔진.
    """

    BBUNG_REACTION_SECONDS = 1.0

    def __init__(self, state: GameState) -> None:
        self.state = state

    def get_current_player(self):
        """
        현재 턴 플레이어를 반환한다.
        """
        current_player_id = self.state.current_turn_player_id

        for player in self.state.players:
            if player.player_id == current_player_id:
                return player

        raise ValueError(
            f"현재 턴 플레이어를 찾을 수 없습니다: {current_player_id}"
        )

    def get_current_player_stops(self):
        """
        현재 턴 플레이어가 선언할 수 있는 STOP 목록을 반환한다.

        STOP 확인은 플레이어가 6장을 가진
        DISCARD 단계에서만 가능하다.

        선언 가능한 STOP이 없으면 빈 리스트를 반환한다.
        """
        if self.state.turn_phase != TurnPhase.DISCARD:
            return []

        player = self.get_current_player()

        if len(player.hand) != 6:
            return []

        return get_available_stops(player.hand)

    def can_player_declare_surprise_stop(
        self,
        player_id: str,
    ) -> bool:
        """
        특정 플레이어가 현재 기습 STOP을
        선언할 수 있는지 확인한다.

        조건:
        - 게임 진행 중
        - 본인 턴
        - DRAW 단계
        - 손패 2장
        - 두 장 합 5 이하
        - 선언자 본인도 뻥 이력이 있음
        - 필요한 뻥 플레이어 수 충족
        """
        if self.state.status != GameStatus.PLAYING:
            return False

        if (
            player_id
            != self.state.current_turn_player_id
        ):
            return False

        if self.state.turn_phase != TurnPhase.DRAW:
            return False

        player = None

        for target in self.state.players:
            if target.player_id == player_id:
                player = target
                break

        if player is None:
            raise ValueError(
                f"플레이어를 찾을 수 없습니다: "
                f"{player_id}"
            )

        return can_declare_surprise_stop(
            player,
            self.state.players,
        )


    def declare_surprise_stop(
        self,
        player_id: str,
    ) -> int:
        """
        현재 플레이어가 기습 STOP을 선언한다.

        조건을 다시 검증한 뒤:
        - 선언자의 기본 점수를 계산한다.
        - 독박 여부를 판정한다.
        - 모든 플레이어의 라운드 점수를 정산한다.
        - 라운드를 종료한다.

        반환값:
            기습 STOP 선언자의 최종 라운드 점수
        """
        if not self.can_player_declare_surprise_stop(
            player_id
        ):
            raise ValueError(
                "현재 기습 STOP을 선언할 수 없습니다."
            )

        player = None

        for target in self.state.players:
            if target.player_id == player_id:
                player = target
                break

        if player is None:
            raise ValueError(
                f"플레이어를 찾을 수 없습니다: "
                f"{player_id}"
            )

        base_score = calculate_two_card_sum(
            player.hand
        )

        has_dokbak = has_surprise_stop_dokbak(
            player=player,
            players=self.state.players,
            hand_score_calculator=(
                calculate_hand_score
            ),
        )

        # 먼저 다른 플레이어 점수를 정산한다.
        for other_player in self.state.players:
            if other_player.player_id == player_id:
                continue

            other_player.round_score = (
                calculate_hand_score(
                    other_player.hand
                )
            )

        # 기습 STOP 선언자 점수
        final_score = base_score

        if has_dokbak:
            final_score += 50

        player.round_score = final_score

        self.state.surprise_stop_dokbak = (
            has_dokbak
        )

        self.finalize_round(
            winner_id=player.player_id,
            reason=RoundEndReason.SURPRISE_STOP,
        )

        return final_score


    def finalize_round(
        self,
        winner_id: str | None,
        reason: RoundEndReason,
    ) -> None:
        """
        현재 라운드의 점수를 최종 확정한다.

        - 각 플레이어의 round_score를 total_score에 반영
        - 라운드 종료 정보 기록
        - 게임 상태를 ROUND_END로 변경
        - 남아 있는 뻥 반응 상태 정리

        같은 라운드는 한 번만 최종 정산할 수 있다.
        """
        if self.state.round_finalized:
            raise ValueError(
                "현재 라운드는 이미 최종 정산되었습니다."
            )

        for player in self.state.players:
            player.total_score += player.round_score

        self.state.round_winner_id = winner_id
        self.state.round_end_reason = reason

        self.state.status = GameStatus.ROUND_END
        self.state.turn_phase = None

        self.state.bbung_candidate_player_ids = []
        self.state.bbung_reaction_deadline = None

        self.state.round_finalized = True


    def determine_next_dealer_id(
        self,
    ) -> str:
        """
        직전 라운드 승자가 다음 라운드의 선을 잡는다.
        """
        if self.state.status != GameStatus.ROUND_END:
            raise ValueError(
                "라운드 종료 상태에서만 "
                "다음 선을 결정할 수 있습니다."
            )

        if not self.state.round_finalized:
            raise ValueError(
                "현재 라운드 정산이 완료되지 않았습니다."
            )

        if (
            self.state.round_number
            >= self.state.max_rounds
        ):
            raise ValueError(
                "마지막 라운드 이후에는 "
                "다음 선을 결정하지 않습니다."
            )

        winner_id = self.state.round_winner_id

        if winner_id is None:
            raise ValueError(
                "이번 라운드 승자가 확정되지 않아 "
                "다음 선을 결정할 수 없습니다."
            )

        return winner_id


    def continue_after_round(
        self,
        next_dealer_id: str | None = None,
    ) -> None:
        """
        라운드 종료 후 다음 단계로 진행한다.

        1~19라운드:
            next_dealer_id를 받아 다음 라운드 시작

        20라운드:
            최종 점수를 판정하고
            단독 우승 또는 타이브레이커로 진행
        """
        if self.state.status != GameStatus.ROUND_END:
            raise ValueError(
                "라운드 종료 상태에서만 "
                "다음 단계로 진행할 수 있습니다."
            )

        if not self.state.round_finalized:
            raise ValueError(
                "현재 라운드 정산이 완료되지 않았습니다."
            )

        # ---------------------------------
        # 마지막 라운드
        # ---------------------------------

        if (
            self.state.round_number
            >= self.state.max_rounds
        ):
            self.start_game_end_sequence()
            return

        # ---------------------------------
        # 일반 다음 라운드
        # ---------------------------------

        if next_dealer_id is None:
            next_dealer_id = (
                self.determine_next_dealer_id()
            )

        self.start_next_round(
            next_dealer_id=next_dealer_id
        )


    def start_next_round(
        self,
        next_dealer_id: str,
    ) -> None:
        """
        종료된 라운드를 정리하고
        다음 라운드를 시작한다.

        기본 규칙은 직전 라운드 승자가 다음 선이다.
        필요하면 next_dealer_id를 명시적으로 전달할 수도 있다.
        """
        if self.state.status != GameStatus.ROUND_END:
            raise ValueError(
                "라운드가 종료된 상태에서만 "
                "다음 라운드를 시작할 수 있습니다."
            )

        if not self.state.round_finalized:
            raise ValueError(
                "현재 라운드의 최종 정산이 "
                "완료되지 않았습니다."
            )

        if self.state.round_number >= self.state.max_rounds:
            raise ValueError(
                "마지막 라운드까지 종료되었습니다."
            )

        dealer = None

        for player in self.state.players:
            if player.player_id == next_dealer_id:
                dealer = player
                break

        if dealer is None:
            raise ValueError(
                f"다음 선 플레이어를 찾을 수 없습니다: "
                f"{next_dealer_id}"
            )

        # --------------------------------------------------
        # 1. 라운드 번호 증가
        # --------------------------------------------------

        self.state.round_number += 1

        # --------------------------------------------------
        # 2. 플레이어별 라운드 상태 초기화
        #
        # total_score는 절대 초기화하지 않는다.
        # --------------------------------------------------

        for player in self.state.players:
            player.hand.clear()

            player.round_score = 0

            player.bbung_count = 0
            player.bbung_months.clear()

        # --------------------------------------------------
        # 3. 라운드 공용 카드 상태 초기화
        # --------------------------------------------------

        self.state.deck = Deck()
        self.state.deck.shuffle()

        self.state.discard_pile.clear()

        self.state.last_discarded_card = None
        self.state.last_discarded_by_player_id = None

        # --------------------------------------------------
        # 4. 뻥 반응 상태 초기화
        # --------------------------------------------------

        self.state.bbung_candidate_player_ids.clear()
        self.state.bbung_reaction_deadline = None

        # --------------------------------------------------
        # 5. 바가지 선언 초기화
        # --------------------------------------------------

        self.state.active_bagaji_declarations.clear()

        self.state.active_bomb_bagaji_declarations.clear()

        # --------------------------------------------------
        # 6. 이전 라운드 종료 정보 초기화
        # --------------------------------------------------

        self.state.round_winner_id = None
        self.state.round_end_reason = None

        self.state.declared_stop_type = None

        self.state.bagaji_victim_id = None
        self.state.triggered_bagaji_month = None

        self.state.surprise_stop_dokbak = False

        self.state.round_finalized = False

        self.state.deck_reshuffle_used = False
        self.state.round_winner_decided_by_tie_break = False

        # --------------------------------------------------
        # 7. 새로운 선 설정
        # --------------------------------------------------

        self.state.dealer_id = dealer.player_id

        self.state.current_turn_player_id = (
            dealer.player_id
        )

        # --------------------------------------------------
        # 8. 새 라운드 카드 분배
        # --------------------------------------------------

        deal_initial_cards(
            deck=self.state.deck,
            players=self.state.players,
            dealer_id=dealer.player_id,
        )

        # 선은 6장을 받은 뒤
        # 드로우 없이 바로 한 장 버린다.
        self.state.turn_phase = TurnPhase.DISCARD

        self.state.status = GameStatus.PLAYING


    def settle_normal_stop_scores(
        self,
        winner_id: str,
    ) -> None:
        """
        일반 STOP 종료 시 STOP 선언자를 제외한
        나머지 플레이어의 라운드 점수를 계산한다.

        현재 단계에서는 각 플레이어 손패의 월 합계를
        그대로 양수 점수로 사용한다.

        폭탄에 의한 점수 보정은 추후 폭탄 규칙에서 처리한다.
        """
        for player in self.state.players:
            if player.player_id == winner_id:
                continue

            player.round_score = calculate_hand_score(
                player.hand
            )

    def can_player_declare_bbung(
        self,
        player_id: str,
        ) -> bool:
        """
        특정 플레이어가 마지막 버림패에 대해
        뻥을 선언할 수 있는지 확인한다.

        뻥에는 반드시:
        - 마지막 버림패와 같은 월 카드 2장
        - 추가로 버릴 카드 1장

        총 최소 3장의 손패가 필요하다.
        """
        if self.state.status != GameStatus.PLAYING:
            return False

        if self.state.turn_phase != TurnPhase.REACTION:
            return False

        discarded_card = self.state.last_discarded_card

        discarded_by_player_id = (
            self.state.last_discarded_by_player_id
        )

        if discarded_card is None:
            return False

        if discarded_by_player_id is None:
            return False

        # 자기 자신이 버린 카드에는
        # 뻥할 수 없다.
        if player_id == discarded_by_player_id:
            return False

        target_player = None

        for player in self.state.players:
            if player.player_id == player_id:
                target_player = player
                break

        if target_player is None:
            raise ValueError(
                f"플레이어를 찾을 수 없습니다: "
                f"{player_id}"
        )

        # ---------------------------------
        # 중요:
        # 뻥에는 같은 월 2장 외에도
        # 추가로 버릴 카드 1장이 필요하다.
        #
        # 따라서 손패가 2장 이하라면
        # 절대 뻥 후보가 될 수 없다.
        # ---------------------------------
        if len(target_player.hand) < 3:
            return False

        return can_declare_bbung(
            target_player.hand,
            discarded_card,
        )


    def refresh_bbung_candidates(
        self,
    ) -> list[str]:
        """
        현재 마지막 버림패에 대해
        뻥 가능한 모든 플레이어를 다시 계산한다.

        반환값:
            뻥 가능한 player_id 목록
        """
        candidate_ids = []

        if self.state.turn_phase != TurnPhase.REACTION:
            self.state.bbung_candidate_player_ids = []
            return []

        for player in self.state.players:
            if self.can_player_declare_bbung(
                player.player_id
            ):
                candidate_ids.append(
                    player.player_id
                )

        self.state.bbung_candidate_player_ids = (
            candidate_ids
        )

        if candidate_ids:
            self.state.bbung_reaction_deadline = (
                datetime.now(timezone.utc)
                + timedelta(
                    seconds=self.BBUNG_REACTION_SECONDS
                )
            )
        else:
            self.state.bbung_reaction_deadline = None

        return candidate_ids


    def is_bbung_reaction_active(self) -> bool:
        """
        현재 실제 뻥 반응 시간이 남아 있는지 확인한다.
        """
        if not self.state.bbung_candidate_player_ids:
            return False

        deadline = self.state.bbung_reaction_deadline

        if deadline is None:
            return False

        return datetime.now(timezone.utc) < deadline


    def clear_expired_bbung_reaction(
        self,
    ) -> None:
        """
        뻥 반응 시간이 만료되었다면
        후보 목록과 종료시각을 정리한다.
        """
        if self.is_bbung_reaction_active():
            return

        self.state.bbung_candidate_player_ids = []
        self.state.bbung_reaction_deadline = None


    def close_bbung_reaction_window(self) -> None:
        """
        뻥 반응 시간이 끝났을 때
        현재 뻥 후보 목록을 닫는다.

        나중에는 서버의 1초 타이머가
        이 함수를 호출하게 된다.
        """
        if self.state.turn_phase != TurnPhase.REACTION:
            raise ValueError(
                "현재는 반응 단계가 아닙니다."
            )

        self.state.bbung_candidate_player_ids = []
        self.state.bbung_reaction_deadline = None
    

    def declare_bbung(
        self,
        player_id: str,
        matching_card_ids: list[str],
        extra_discard_card_id: str,
    ):
        """
        특정 플레이어가 마지막 버림패에 대해 뻥을 선언한다.

        뻥 선언 시:
        - 마지막 버림패와 같은 월 카드 2장
        - 추가로 버릴 카드 1장

        총 3장을 손패에서 한 번에 제거하고
        버림패 영역으로 이동한다.

        이번 단계에서는 뻥 이후의 턴 진행은 처리하지 않는다.
        """
        if self.state.status != GameStatus.PLAYING:
            raise ValueError(
                "현재는 진행 중인 라운드가 아닙니다."
            )

        if self.state.turn_phase != TurnPhase.REACTION:
            raise ValueError(
                "현재는 뻥을 선언할 수 있는 반응 단계가 아닙니다."
            )

        if not self.can_player_declare_bbung(player_id):
            raise ValueError(
                "현재 이 플레이어는 뻥을 선언할 수 없습니다."
            )

        if len(matching_card_ids) != 2:
            raise ValueError(
                "뻥에는 같은 월 카드가 정확히 2장 필요합니다."
            )

        if len(set(matching_card_ids)) != 2:
            raise ValueError(
                "같은 카드를 중복해서 선택할 수 없습니다."
            )

        if extra_discard_card_id in matching_card_ids:
            raise ValueError(
                "추가 버림 카드는 뻥 카드 2장과 달라야 합니다."
            )

        player = None

        for target in self.state.players:
            if target.player_id == player_id:
                player = target
                break

        if player is None:
            raise ValueError(
                f"플레이어를 찾을 수 없습니다: "
                f"{player_id}"
            )

        discarded_card = self.state.last_discarded_card

        if discarded_card is None:
            raise ValueError(
                "뻥 대상이 되는 마지막 버림패가 없습니다."
            )

        selected_matching_cards = []

        for card_id in matching_card_ids:
            selected_card = next(
                (
                    card
                    for card in player.hand
                    if card.card_id == card_id
                ),
                None,
            )

            if selected_card is None:
                raise ValueError(
                    f"손패에 없는 카드입니다: "
                    f"{card_id}"
                )

            if selected_card.month != discarded_card.month:
                raise ValueError(
                    "뻥 카드의 월이 마지막 버림패와 다릅니다."
                )

            selected_matching_cards.append(
                selected_card
            )

        extra_discard_card = next(
            (
                card
                for card in player.hand
                if card.card_id == extra_discard_card_id
            ),
            None,
        )

        if extra_discard_card is None:
            raise ValueError(
                f"추가로 버릴 카드가 손패에 없습니다: "
                f"{extra_discard_card_id}"
            )

        # 모든 검증이 끝난 뒤에만 실제 상태를 변경한다.
        # 중간에 검증 실패가 나더라도 손패가 일부만 빠지는 일을 막는다.
        cards_to_discard = (
            selected_matching_cards
            + [extra_discard_card]
        )

        for card in cards_to_discard:
            player.hand.remove(card)

        self.state.discard_pile.extend(
            cards_to_discard
        )

        # 이번 라운드의 뻥 이력을 기록한다.
        player.bbung_count += 1
        player.bbung_months.append(
            discarded_card.month
        )

        # 뻥으로 손패가 바뀌었으므로
        # 기존 바가지 선언의 유효성을 다시 검사한다.
        self.refresh_active_bagaji_declarations()

        # 뻥하면서 추가로 버린 카드가
        # 새로운 반응 대상이 된다.
        self.state.last_discarded_card = (
            extra_discard_card
        )

        self.state.last_discarded_by_player_id = (
            player.player_id
        )

        # 뻥한 사람을 현재 턴의 기준점으로 변경한다.
        self.state.current_turn_player_id = (
            player.player_id
        )

        # 추가 버림패에 다시 뻥할 수 있으므로
        # REACTION 상태를 유지한다.
        self.state.turn_phase = TurnPhase.REACTION

        # 뻥하면서 추가로 버린 카드에 대해
        # 다시 다른 플레이어들의 뻥 가능 여부를 검사한다.
        self.refresh_bbung_candidates()

        return cards_to_discard


    def refresh_active_bagaji_declarations(
        self,
    ) -> None:
        """
        활성 바가지 선언의 대상 페어가 아직 유지되는지 검사한다.

        핵심 규칙:
        - 선언 대상 월 카드 2장이 모두 남아 있으면 선언 유지
        - 그 2장 중 하나라도 사용해서 대상 월 카드가 1장 이하가 되면
          해당 바가지는 즉시 자동 철회

        손패 장수가 늘거나 다른 월 카드를 버린 것만으로는
        바가지 선언을 자동 철회하지 않는다.

        일반 바가지와 폭탄 바가지 모두
        '바가지 대상 월의 2장'을 기준으로 같은 규칙을 적용한다.
        """
        players_by_id = {
            player.player_id: player
            for player in self.state.players
        }

        self.state.active_bagaji_declarations = [
            declaration
            for declaration
            in self.state.active_bagaji_declarations
            if (
                declaration.player_id
                in players_by_id
                and sum(
                    1
                    for card
                    in players_by_id[
                        declaration.player_id
                    ].hand
                    if (
                        card.month
                        == declaration.month
                    )
                )
                >= 2
            )
        ]

        self.state.active_bomb_bagaji_declarations = [
            declaration
            for declaration
            in self.state.active_bomb_bagaji_declarations
            if (
                declaration.player_id
                in players_by_id
                and sum(
                    1
                    for card
                    in players_by_id[
                        declaration.player_id
                    ].hand
                    if (
                        card.month
                        == declaration.month
                    )
                )
                >= 2
            )
        ]


    def _player_has_active_bagaji(
        self,
        player_id: str,
    ) -> bool:
        """
        플레이어가 일반/폭탄을 합쳐
        이미 활성 바가지 하나를 가지고 있는지 확인한다.
        """
        has_general = any(
            declaration.player_id == player_id
            for declaration
            in self.state.active_bagaji_declarations
        )

        has_bomb = any(
            declaration.player_id == player_id
            for declaration
            in self.state.active_bomb_bagaji_declarations
        )

        return has_general or has_bomb


    def declare_general_bagaji(
        self,
        player_id: str,
        month: int,
    ) -> BagajiDeclaration:
        """
        특정 플레이어가 일반 바가지를 선언한다.

        조건:
        - 게임 진행 중
        - 이번 라운드에 뻥 이력이 있음
        - 현재 손패가 정확히 2장
        - 그 2장이 선언 대상 월의 같은 패
        - 플레이어당 활성 바가지는 일반/폭탄을 합쳐 최대 1개

        선언은 현재 턴과 무관하게 가능하고,
        직접 철회하거나 조건이 깨질 때까지 활성 상태로 유지된다.
        """
        if self.state.status != GameStatus.PLAYING:
            raise ValueError(
                "현재는 진행 중인 라운드가 아닙니다."
            )

        player = next(
            (
                target
                for target in self.state.players
                if target.player_id == player_id
            ),
            None,
        )

        if player is None:
            raise ValueError(
                f"플레이어를 찾을 수 없습니다: "
                f"{player_id}"
            )

        self.refresh_active_bagaji_declarations()

        if self._player_has_active_bagaji(player_id):
            raise ValueError(
                "이미 활성 바가지를 선언한 상태입니다."
            )

        if len(player.hand) != 2:
            raise ValueError(
                "일반 바가지는 손패가 정확히 2장일 때만 "
                "선언할 수 있습니다."
            )

        if player.bbung_count <= 0:
            raise ValueError(
                "일반 바가지는 이번 라운드에 뻥을 한 "
                "플레이어만 선언할 수 있습니다."
            )

        matching_count = sum(
            1
            for card in player.hand
            if card.month == month
        )

        if matching_count != 2:
            raise ValueError(
                "일반 바가지는 남은 2장의 손패가 "
                "같은 월이어야 합니다."
            )

        if not can_declare_general_bagaji(
            player,
            month,
        ):
            raise ValueError(
                "현재 조건으로는 일반 바가지를 "
                "선언할 수 없습니다."
            )

        declaration = BagajiDeclaration(
            player_id=player_id,
            month=month,
        )

        self.state.active_bagaji_declarations.append(
            declaration
        )

        return declaration


    def cancel_general_bagaji(
        self,
        player_id: str,
    ) -> BagajiDeclaration:
        """
        플레이어의 활성 일반 바가지 선언을 직접 철회한다.

        철회 후 나중에 조건이 다시 성립하면
        같은 월도 다시 선언할 수 있다.
        """
        if self.state.status != GameStatus.PLAYING:
            raise ValueError(
                "현재는 진행 중인 라운드가 아닙니다."
            )

        declaration = next(
            (
                declaration
                for declaration
                in self.state.active_bagaji_declarations
                if declaration.player_id == player_id
            ),
            None,
        )

        if declaration is None:
            raise ValueError(
                "철회할 일반 바가지 선언이 없습니다."
            )

        self.state.active_bagaji_declarations.remove(
            declaration
        )

        return declaration


    def declare_bomb_bagaji(
        self,
        player_id: str,
        month: int,
    ) -> BombBagajiDeclaration:
        """
        특정 플레이어가 폭탄 바가지를 선언한다.

        조건:
        - 현재 손패가 정확히 5장
        - 선언 대상 월 카드가 정확히 2장
        - 그와 다른 월 카드가 정확히 3장
        - 3장 쪽 월이 폭탄
        - 뻥 이력은 필요 없음
        - 플레이어당 활성 바가지는 일반/폭탄을 합쳐 최대 1개
        """
        if self.state.status != GameStatus.PLAYING:
            raise ValueError(
                "현재는 진행 중인 라운드가 아닙니다."
            )

        player = next(
            (
                target
                for target in self.state.players
                if target.player_id == player_id
            ),
            None,
        )

        if player is None:
            raise ValueError(
                f"플레이어를 찾을 수 없습니다: "
                f"{player_id}"
            )

        self.refresh_active_bagaji_declarations()

        if self._player_has_active_bagaji(player_id):
            raise ValueError(
                "이미 활성 바가지를 선언한 상태입니다."
            )

        if len(player.hand) != 5:
            raise ValueError(
                "폭탄 바가지는 손패가 정확히 5장일 때만 "
                "선언할 수 있습니다."
            )

        pair_count = sum(
            1
            for card in player.hand
            if card.month == month
        )

        if pair_count != 2:
            raise ValueError(
                "폭탄 바가지 대상 월은 정확히 2장이어야 합니다."
            )

        bomb_months = []

        for candidate_month in range(1, 13):
            if candidate_month == month:
                continue

            candidate_count = sum(
                1
                for card in player.hand
                if card.month == candidate_month
            )

            if candidate_count == 3:
                bomb_months.append(candidate_month)

        if len(bomb_months) != 1:
            raise ValueError(
                "폭탄 바가지는 다른 한 월의 카드가 "
                "정확히 3장이어야 합니다."
            )

        if not can_declare_bomb_bagaji(
            player,
            month,
        ):
            raise ValueError(
                "현재 조건으로는 폭탄 바가지를 "
                "선언할 수 없습니다."
            )

        bomb_month = bomb_months[0]

        declaration = BombBagajiDeclaration(
            player_id=player_id,
            month=month,
            bomb_month=bomb_month,
        )

        self.state.active_bomb_bagaji_declarations.append(
            declaration
        )

        return declaration


    def cancel_bomb_bagaji(
        self,
        player_id: str,
    ) -> BombBagajiDeclaration:
        """
        플레이어의 활성 폭탄 바가지 선언을 직접 철회한다.

        철회 후 나중에 조건이 다시 성립하면
        같은 조합도 다시 선언할 수 있다.
        """
        if self.state.status != GameStatus.PLAYING:
            raise ValueError(
                "현재는 진행 중인 라운드가 아닙니다."
            )

        declaration = next(
            (
                declaration
                for declaration
                in self.state.active_bomb_bagaji_declarations
                if declaration.player_id == player_id
            ),
            None,
        )

        if declaration is None:
            raise ValueError(
                "철회할 폭탄 바가지 선언이 없습니다."
            )

        self.state.active_bomb_bagaji_declarations.remove(
            declaration
        )

        return declaration


    def get_triggered_bagaji_declarations(
        self,
        discarded_card,
        discarded_by_player_id: str,
    ) -> list[BagajiDeclaration]:
        """
        특정 버림패로 발동 조건을 만족한
        일반 바가지 선언들을 모두 반환한다.

        같은 월에 여러 플레이어가 바가지를 선언한 경우
        모두 반환한다.

        단, 자기 자신이 버린 카드로
        자기 바가지가 발동되지는 않는다.
        """
        triggered = []

        for declaration in (
            self.state.active_bagaji_declarations
        ):
            if (
                declaration.month
                != discarded_card.month
            ):
                continue

            if (
                declaration.player_id
                == discarded_by_player_id
            ):
                continue

            triggered.append(
                declaration
            )

        return triggered

    def get_triggered_bomb_bagaji_declarations(
        self,
        discarded_card,
        discarded_by_player_id: str,
    ) -> list[BombBagajiDeclaration]:
        """
        특정 버림패로 발동 조건을 만족한
        폭탄 바가지 선언들을 반환한다.

        자기 자신이 버린 카드로
        자기 폭탄 바가지는 발동하지 않는다.
        """
        triggered = []

        for declaration in (
            self.state.active_bomb_bagaji_declarations
        ):
            if (
                declaration.month
                != discarded_card.month
            ):
                continue

            if (
                declaration.player_id
                == discarded_by_player_id
            ):
                continue

            triggered.append(
                declaration
            )

        return triggered


    def settle_general_bagaji(
        self,
        winner_id: str,
        victim_id: str,
        month: int,
    ) -> None:
        """
        일반 바가지가 성립했을 때
        모든 플레이어의 라운드 점수를 정산한다.

        바가지 성공자:
            0점

        바가지 피해자:
            현재 손패 점수 + 30점

        나머지 플레이어:
            현재 손패 점수
        """
        for player in self.state.players:
            if player.player_id == winner_id:
                player.round_score = 0
                continue

            hand_score = calculate_hand_score(
                player.hand
            )

            if player.player_id == victim_id:
                player.round_score = (
                    hand_score + 30
                )
            else:
                player.round_score = hand_score

        self.state.bagaji_victim_id = victim_id
        self.state.triggered_bagaji_month = month

        self.finalize_round(
            winner_id=winner_id,
            reason=RoundEndReason.BAGAJI,
        )
    

    def settle_bomb_bagaji(
        self,
        winner_id: str,
        victim_id: str,
        month: int,
    ) -> None:
        """
        폭탄 바가지가 성립했을 때
        모든 플레이어의 라운드 점수를 정산한다.

        폭탄 바가지 성공자:
            0점

        피해자:
            현재 손패 점수 + 30점

        나머지 플레이어:
            현재 손패 점수
        """
        for player in self.state.players:
            if player.player_id == winner_id:
                player.round_score = 0
                continue

            hand_score = calculate_hand_score(
                player.hand
            )

            if player.player_id == victim_id:
                player.round_score = (
                    hand_score + 30
                )
            else:
                player.round_score = hand_score

        self.state.bagaji_victim_id = victim_id
        self.state.triggered_bagaji_month = month

        self.finalize_round(
            winner_id=winner_id,
            reason=RoundEndReason.BOMB_BAGAJI,
        )


    def check_bagaji_after_discard(
        self,
        discarded_card,
        discarded_by_player_id: str,
    ) -> bool:
        """
        방금 버린 카드로 일반 바가지 또는
        폭탄 바가지가 발동하는지 검사한다.

        발동하면 즉시 정산하고 True를 반환한다.
        """
        general_triggered = (
            self.get_triggered_bagaji_declarations(
                discarded_card=discarded_card,
                discarded_by_player_id=(
                    discarded_by_player_id
                ),
            )
        )

        bomb_triggered = (
            self.get_triggered_bomb_bagaji_declarations(
                discarded_card=discarded_card,
                discarded_by_player_id=(
                    discarded_by_player_id
                ),
            )
        )

        if (
            not general_triggered
            and not bomb_triggered
        ):
            return False

        # 서로 다른 플레이어의 바가지가
        # 하나의 버림패에 동시에 발동하는 상태는
        # 정상적인 48장 카드 구성에서는 발생하면 안 된다.
        winner_ids = {
            declaration.player_id
            for declaration in (
                general_triggered
                + bomb_triggered
            )
        }

        if len(winner_ids) > 1:
            raise ValueError(
                "하나의 버림패에 서로 다른 플레이어의 "
                "바가지가 동시에 발동했습니다."
            )

        # 같은 플레이어에게 일반 바가지와 폭탄 바가지가
        # 동시에 잡히는 경우는 아직 우선순위 규칙을
        # 확정하지 않았으므로 조용히 임의 처리하지 않는다.
        if general_triggered and bomb_triggered:
            raise ValueError(
                "같은 버림패에 일반 바가지와 "
                "폭탄 바가지가 동시에 발동했습니다."
            )

        if bomb_triggered:
            declaration = bomb_triggered[0]

            self.settle_bomb_bagaji(
                winner_id=declaration.player_id,
                victim_id=discarded_by_player_id,
                month=declaration.month,
            )

            return True

        declaration = general_triggered[0]

        self.settle_general_bagaji(
            winner_id=declaration.player_id,
            victim_id=discarded_by_player_id,
            month=declaration.month,
        )

        return True

    def declare_stop(
        self,
        selected_stop_type: StopType,
    ) -> int:
        """
        현재 턴 플레이어가 STOP을 선언한다.

        선택한 STOP이 현재 손패에서 실제로 가능한지 검증한 뒤
        점수를 계산하고 라운드를 종료한다.

        반환값:
            선언한 플레이어의 STOP 점수
        """
        if self.state.status != GameStatus.PLAYING:
            raise ValueError(
                "현재는 진행 중인 라운드가 아닙니다."
            )

        if self.state.turn_phase != TurnPhase.DISCARD:
            raise ValueError(
                "현재 단계에서는 STOP을 선언할 수 없습니다."
            )

        player = self.get_current_player()

        if len(player.hand) != 6:
            raise ValueError(
                "STOP 선언은 6장의 손패가 필요합니다."
            )

        available_stops = get_available_stops(
            player.hand
        )

        if selected_stop_type not in available_stops:
            raise ValueError(
                f"현재 선언할 수 없는 STOP입니다: "
                f"{selected_stop_type.value}"
            )

        score = calculate_stop_score(
            player.hand,
            selected_stop_type,
        )

        player.round_score = score

        self.settle_normal_stop_scores(
            winner_id=player.player_id,
        )

        self.state.declared_stop_type = (
            selected_stop_type.value
        )

        self.finalize_round(
            winner_id=player.player_id,
            reason=RoundEndReason.NORMAL_STOP,
        )

        return score

    def _get_next_player_id(
        self,
        player_id: str,
    ) -> str:
        """
        지정한 플레이어의 다음 순서 플레이어 ID를 반환한다.
        """
        for index, player in enumerate(
            self.state.players
        ):
            if player.player_id == player_id:
                next_index = (
                    index + 1
                ) % len(self.state.players)

                return (
                    self.state.players[
                        next_index
                    ].player_id
                )

        raise ValueError(
            f"플레이어를 찾을 수 없습니다: "
            f"{player_id}"
        )


    def _resolve_round_three_card_tie(
        self,
        player_ids: list[str],
    ) -> str:
        """
        라운드 종료 최저점 동점자들이
        별도 덱에서 3장씩 뽑고,
        월 합계가 가장 높은 사람이 승리한다.

        최고점이 다시 동점이면
        해당 동점자들만 새 덱으로 반복한다.
        """
        contenders = list(player_ids)

        if len(contenders) < 2:
            if not contenders:
                raise ValueError(
                    "3장 승부 참가자가 없습니다."
                )

            return contenders[0]

        while True:
            tie_deck = Deck()
            tie_deck.shuffle()

            scores = {}

            for player_id in contenders:
                drawn_cards = [
                    tie_deck.draw()
                    for _ in range(3)
                ]

                scores[player_id] = sum(
                    card.month
                    for card in drawn_cards
                )

            highest_score = max(
                scores.values()
            )

            winners = [
                player_id
                for player_id, score
                in scores.items()
                if score == highest_score
            ]

            if len(winners) == 1:
                return winners[0]

            contenders = winners


    def settle_deck_exhausted_round(
        self,
        determine_winner: bool = False,
    ) -> None:
        """
        덱 소진으로 라운드가 끝났을 때
        모든 플레이어의 현재 손패 점수를 계산한다.

        determine_winner=True:
        - 가장 낮은 손패 점수가 라운드 승자
        - 최저점 동점이면 별도 3장 승부
        """
        for player in self.state.players:
            player.round_score = (
                calculate_hand_score(
                    player.hand
                )
            )

        winner_id = None

        if determine_winner:
            lowest_score = min(
                player.round_score
                for player in self.state.players
            )

            lowest_players = [
                player
                for player in self.state.players
                if player.round_score
                == lowest_score
            ]

            if len(lowest_players) == 1:
                winner_id = (
                    lowest_players[0].player_id
                )
                self.state.round_winner_decided_by_tie_break = False
            else:
                winner_id = (
                    self._resolve_round_three_card_tie(
                        [
                            player.player_id
                            for player in lowest_players
                        ]
                    )
                )
                self.state.round_winner_decided_by_tie_break = True

        self.finalize_round(
            winner_id=winner_id,
            reason=RoundEndReason.DECK_EXHAUSTED,
        )


    def handle_empty_deck(self) -> bool:
        """
        드로우 직전에 덱이 비어 있을 때 처리한다.

        3~4인:
        - 1페이즈 소진 즉시 현재 손패 최저점 승리
        - 최저점 동점이면 별도 3장 승부

        5~6인:
        - 1페이즈 소진: 버림패 전체를 셔플해 2페이즈 덱 생성
        - 2페이즈 소진: 현재 손패 최저점 승리
          (동점이면 별도 3장 승부)
        """
        if self.state.deck is None:
            raise ValueError(
                "현재 라운드에 덱이 없습니다."
            )

        if self.state.deck.cards:
            return True

        player_count = len(
            self.state.players
        )

        # 3~4인은 첫 덱 소진에서 바로 라운드 종료.
        if player_count in (3, 4):
            self.settle_deck_exhausted_round(
                determine_winner=True
            )
            return False

        # 5~6인은 첫 덱 소진 후 버림패를 다시 섞어
        # 같은 라운드의 2페이즈로 진행한다.
        if (
            player_count in (5, 6)
            and not self.state.deck_reshuffle_used
        ):
            if not self.state.discard_pile:
                self.settle_deck_exhausted_round(
                    determine_winner=True
                )
                return False

            last_discarder_id = (
                self.state.last_discarded_by_player_id
            )

            next_player_id = None

            if last_discarder_id is not None:
                next_player_id = (
                    self._get_next_player_id(
                        last_discarder_id
                    )
                )

            reshuffled_cards = list(
                self.state.discard_pile
            )

            self.state.discard_pile.clear()

            self.state.deck = Deck()
            self.state.deck.cards = reshuffled_cards
            self.state.deck.shuffle()

            self.state.deck_reshuffle_used = True

            if next_player_id is not None:
                self.state.current_turn_player_id = (
                    next_player_id
                )

            self.state.turn_phase = TurnPhase.DRAW

            self.state.last_discarded_card = None
            self.state.last_discarded_by_player_id = None
            self.state.bbung_candidate_player_ids = []
            self.state.bbung_reaction_deadline = None

            return True

        # 5~6인 2페이즈 덱까지 소진되면 라운드 종료.
        if (
            player_count in (5, 6)
            and self.state.deck_reshuffle_used
        ):
            self.settle_deck_exhausted_round(
                determine_winner=True
            )
            return False

        raise ValueError(
            f"지원하지 않는 플레이어 수입니다: "
            f"{player_count}"
        )


    def draw_card(self):
        """
        현재 턴 플레이어가 덱에서 카드 1장을 뽑는다.

        덱이 비어 있는 경우:
        - 3~4인 첫 소진: 최저 손패 점수로 라운드 종료
        - 5~6인 첫 소진: 버림패로 2페이즈 시작
        - 5~6인 두 번째 소진: 최저 손패 점수로 라운드 종료

        라운드가 덱 소진으로 끝난 경우 None을 반환한다.
        """
        if self.state.deck is None:
            raise ValueError(
                "현재 라운드에 덱이 없습니다."
            )

        if self.state.turn_phase != TurnPhase.DRAW:
            raise ValueError(
                f"현재는 드로우 단계가 아닙니다: "
                f"{self.state.turn_phase}"
            )

        can_continue = self.handle_empty_deck()

        if not can_continue:
            return None

        player = self.get_current_player()

        card = self.state.deck.draw()

        player.hand.append(card)

        # 드로우로 선언한 페어가 3장이 되는 등
        # 바가지 조건이 깨졌다면 자동 해제한다.
        self.refresh_active_bagaji_declarations()

        self.state.turn_phase = TurnPhase.DISCARD

        return card

    def discard_card(self, card_id: str):
        """
        현재 턴 플레이어가 손패에서 카드 1장을 버린다.
        """
        if self.state.turn_phase != TurnPhase.DISCARD:
            raise ValueError(
                f"현재는 버리기 단계가 아닙니다: "
                f"{self.state.turn_phase}"
            )

        player = self.get_current_player()

        selected_card = None

        for card in player.hand:
            if card.card_id == card_id:
                selected_card = card
                break

        if selected_card is None:
            raise ValueError(
                f"손패에 존재하지 않는 카드입니다: {card_id}"
            )

        player.hand.remove(selected_card)
        self.state.discard_pile.append(selected_card)

        self.state.last_discarded_card = selected_card
        self.state.last_discarded_by_player_id = (
            player.player_id
        )

        # 버린 플레이어 자신의 손패가 바뀌었으므로
        # 조건이 깨진 활성 바가지는 먼저 자동 해제한다.
        # 다른 플레이어의 유효한 바가지는 그대로 남으므로
        # 바로 아래 발동 검사에는 영향을 주지 않는다.
        self.refresh_active_bagaji_declarations()

        # 바가지는 이미 선언된 상태이므로
        # 버림패가 조건을 만족하는 순간 즉시 발동한다.
        bagaji_triggered = (
            self.check_bagaji_after_discard(
                discarded_card=selected_card,
                discarded_by_player_id=(
                    player.player_id
                ),
            )
        )

        if bagaji_triggered:
            return selected_card

        # 바가지가 발생하지 않았을 때만
        # 뻥 반응 단계로 넘어간다.
        self.state.turn_phase = TurnPhase.REACTION

        self.refresh_bbung_candidates()

        return selected_card

    def advance_turn(self) -> None:
        """
        현재 턴을 다음 플레이어에게 넘긴다.

        마지막 플레이어 다음에는 다시 첫 번째 플레이어로 돌아간다.
        """

        if self.state.turn_phase != TurnPhase.REACTION:
            raise ValueError(
                f"아직 턴을 넘길 수 없습니다: "
                f"{self.state.turn_phase}"
            )

        if self.is_bbung_reaction_active():
            raise ValueError(
                "뻥 반응 시간이 남아 있어 "
                "아직 다음 턴으로 넘어갈 수 없습니다."
            )

        self.clear_expired_bbung_reaction()

        current_player_id = self.state.current_turn_player_id

        current_index = None

        for index, player in enumerate(self.state.players):
            if player.player_id == current_player_id:
                current_index = index
                break

        if current_index is None:
            raise ValueError(
                f"현재 턴 플레이어를 찾을 수 없습니다: "
                f"{current_player_id}"
            )

        next_index = (current_index + 1) % len(self.state.players)

        self.state.current_turn_player_id = (
            self.state.players[next_index].player_id
        )

        self.state.bbung_candidate_player_ids = []
        self.state.turn_phase = TurnPhase.DRAW


    def start_game_end_sequence(self) -> None:
        """
        20라운드 종료 후
        최종 우승자를 판정한다.

        단독 최저점:
            바로 GAME_END

        최저점 동점:
            TIE_BREAK 진입
        """
        if self.state.status != GameStatus.ROUND_END:
            raise ValueError(
                "라운드 종료 상태에서만 "
                "최종 승자 판정을 할 수 있습니다."
            )

        if not self.state.round_finalized:
            raise ValueError(
                "현재 라운드 정산이 완료되지 않았습니다."
            )

        if self.state.round_number < self.state.max_rounds:
            raise ValueError(
                "아직 마지막 라운드가 아닙니다."
            )

        lowest_score = min(
            player.total_score
            for player in self.state.players
        )

        tied_players = [
            player
            for player in self.state.players
            if player.total_score == lowest_score
        ]

        if len(tied_players) == 1:
            winner = tied_players[0]

            self.state.game_winner_id = (
                winner.player_id
            )

            self.state.tie_break_player_ids.clear()
            self.state.tie_break_drawn_cards.clear()

            self.state.status = GameStatus.GAME_END
            self.state.turn_phase = None

            return

        self.state.tie_break_player_ids = [
            player.player_id
            for player in tied_players
        ]

        self.state.tie_break_drawn_cards = {
            player.player_id: []
            for player in tied_players
        }

        self.state.tie_break_current_player_index = 0
        self.state.tie_break_round_number = 1

        self.state.tie_break_deck = Deck()
        self.state.tie_break_deck.shuffle()

        self.state.game_winner_id = None

        self.state.status = GameStatus.TIE_BREAK
        self.state.turn_phase = None



    def get_current_tie_break_player_id(
        self,
    ) -> str:
        """
        현재 타이브레이커에서
        카드를 뽑아야 하는 플레이어 ID를 반환한다.
        """
        if self.state.status != GameStatus.TIE_BREAK:
            raise ValueError(
                "현재 타이브레이커 상태가 아닙니다."
            )

        if not self.state.tie_break_player_ids:
            raise ValueError(
                "타이브레이커 참가자가 없습니다."
            )

        return self.state.tie_break_player_ids[
            self.state.tie_break_current_player_index
        ]


    def get_tie_break_score(
        self,
        player_id: str,
    ) -> int:
        """
        타이브레이커에서 해당 플레이어가
        뽑은 카드들의 월 합계를 반환한다.
        """
        cards = self.state.tie_break_drawn_cards.get(
            player_id
        )

        if cards is None:
            raise ValueError(
                "타이브레이커 참가자가 아닙니다."
            )

        return sum(
            card.month
            for card in cards
        )


    def draw_tie_break_card(
        self,
        player_id: str,
        ) -> Card:
        """
        현재 순서의 플레이어가
        타이브레이커 카드 1장을 공개 드로우한다.

        모든 참가자가 3장씩 뽑으면
        자동으로 승자를 판정한다.
        """
        if self.state.status != GameStatus.TIE_BREAK:
            raise ValueError(
                "현재 타이브레이커 상태가 아닙니다."
            )

        current_player_id = (
            self.get_current_tie_break_player_id()
        )

        if player_id != current_player_id:
            raise ValueError(
                "현재 타이브레이커 드로우 순서가 "
                "아닙니다."
            )

        if self.state.tie_break_deck is None:
            raise ValueError(
                "타이브레이커 덱이 없습니다."
            )

        player_cards = (
            self.state.tie_break_drawn_cards[
                player_id
            ]
        )

        if len(player_cards) >= 3:
            raise ValueError(
                "이미 타이브레이커 카드 "
                "3장을 모두 뽑았습니다."
            )

        card = self.state.tie_break_deck.draw()

        player_cards.append(card)

        # 다음 참가자 순서로 이동
        player_count = len(
            self.state.tie_break_player_ids
        )

        self.state.tie_break_current_player_index = (
            self.state.tie_break_current_player_index
            + 1
        ) % player_count

        # 모두 3장씩 뽑았는지 확인
        all_finished = all(
            len(
                self.state.tie_break_drawn_cards[
                    target_player_id
                ]
            ) == 3
            for target_player_id
            in self.state.tie_break_player_ids
        )

        if all_finished:
            self.resolve_tie_break()

        return card


    def resolve_tie_break(self) -> None:
        """
        모든 참가자가 3장씩 뽑은 뒤
        월 합계가 가장 높은 플레이어를 찾는다.

        단독 최고점:
            GAME_END

        최고점 동점:
            해당 동점자들만 새 타이브레이커
        """
        if self.state.status != GameStatus.TIE_BREAK:
            raise ValueError(
                "현재 타이브레이커 상태가 아닙니다."
            )

        for player_id in (
            self.state.tie_break_player_ids
        ):
            if len(
                self.state.tie_break_drawn_cards[
                    player_id
                ]
            ) != 3:
                raise ValueError(
                    "아직 모든 참가자가 "
                    "3장을 뽑지 않았습니다."
                )

        scores = {
            player_id: self.get_tie_break_score(
                player_id
            )
            for player_id
            in self.state.tie_break_player_ids
        }

        highest_score = max(
            scores.values()
        )

        winners = [
            player_id
            for player_id, score
            in scores.items()
            if score == highest_score
        ]

        # ---------------------------------
        # 단독 승자
        # ---------------------------------

        if len(winners) == 1:
            self.state.game_winner_id = (
                winners[0]
            )

            self.state.status = (
                GameStatus.GAME_END
            )

            self.state.tie_break_current_player_index = 0

            return

        # ---------------------------------
        # 또 동점
        # 동점자들만 재대결
        # ---------------------------------

        self.state.tie_break_player_ids = (
            winners
        )

        self.state.tie_break_drawn_cards = {
            player_id: []
            for player_id in winners
        }

        self.state.tie_break_current_player_index = 0

        self.state.tie_break_round_number += 1

        self.state.tie_break_deck = Deck()
        self.state.tie_break_deck.shuffle()

        self.state.game_winner_id = None


    def play_beginner_ai_discard(
        self,
        player_id: str,
    ):
        """
        초보 AI가 현재 DISCARD 단계에서
        버릴 카드를 선택하고 실제로 버린다.
        """
        if self.state.status != GameStatus.PLAYING:
            raise ValueError(
                "현재는 진행 중인 라운드가 아닙니다."
            )

        if self.state.turn_phase != TurnPhase.DISCARD:
            raise ValueError(
                "현재는 버리기 단계가 아닙니다."
            )

        if (
            self.state.current_turn_player_id
            != player_id
        ):
            raise ValueError(
                "현재 턴 플레이어가 아닙니다."
            )

        player = None

        for target in self.state.players:
            if target.player_id == player_id:
                player = target
                break

        if player is None:
            raise ValueError(
                f"플레이어를 찾을 수 없습니다: "
                f"{player_id}"
            )

        if player.player_type != PlayerType.BOT:
            raise ValueError(
                "AI 플레이어만 사용할 수 있습니다."
            )

        if (
            player.ai_difficulty
            not in (
                AIDifficulty.BEGINNER,
                AIDifficulty.INTERMEDIATE,
                AIDifficulty.ADVANCED,
                AIDifficulty.TAZZA,
            )
        ):
            raise ValueError(
                "현재 함수는 초보/중수/고수/타짜 AI 전용입니다."
            )

        if (
            player.ai_difficulty
            == AIDifficulty.TAZZA
        ):
            selected_card = (
                choose_tazza_discard(
                    player,
                    self.state.discard_pile,
                )
            )
        elif (
            player.ai_difficulty
            in (
                AIDifficulty.ADVANCED,
                AIDifficulty.TAZZA,
            )
        ):
            selected_card = (
                choose_advanced_discard(
                    player,
                    self.state.discard_pile,
                )
            )
        elif (
            player.ai_difficulty
            == AIDifficulty.INTERMEDIATE
        ):
            selected_card = (
                choose_intermediate_discard(
                    player
                )
            )
        else:
            selected_card = (
                choose_beginner_discard(
                    player
                )
            )

        self.discard_card(
            selected_card.card_id
        )

        # 버리기로 인해 라운드가 끝나지 않았다면
        # 현재 남은 손패가 바가지 조건인지 확인한다.
        #
        # 예:
        # [3,3,3,7,7,9]
        # → 9월 버림
        # → [3,3,3,7,7]
        # → 7월 폭탄 바가지 자동 선언
        if self.state.status == GameStatus.PLAYING:
            self.try_beginner_ai_bagaji(
                player.player_id
            )

        return selected_card


    def try_beginner_ai_surprise_stop(
        self,
        player_id: str,
    ) -> bool:
        """
        초보 AI가 현재 턴 시작의 DRAW 단계에서
        기습 STOP이 가능하면 즉시 선언한다.

        반환값:
            True:
                기습 STOP 선언으로 라운드 종료

            False:
                현재 기습 STOP 선언 불가
        """
        if self.state.status != GameStatus.PLAYING:
            return False

        if (
            self.state.current_turn_player_id
            != player_id
        ):
            return False

        if self.state.turn_phase != TurnPhase.DRAW:
            return False

        player = None

        for target in self.state.players:
            if target.player_id == player_id:
                player = target
                break

        if player is None:
            raise ValueError(
                f"플레이어를 찾을 수 없습니다: "
                f"{player_id}"
            )

        if player.player_type != PlayerType.BOT:
            raise ValueError(
                "AI 플레이어만 사용할 수 있습니다."
            )

        if (
            player.ai_difficulty
            not in (
                AIDifficulty.BEGINNER,
                AIDifficulty.INTERMEDIATE,
                AIDifficulty.ADVANCED,
                AIDifficulty.TAZZA,
            )
        ):
            raise ValueError(
                "현재 함수는 초보/중수/고수/타짜 AI 전용입니다."
            )

        if not self.can_player_declare_surprise_stop(
            player_id
        ):
            return False

        if (
            player.ai_difficulty
            == AIDifficulty.TAZZA
        ):
            if not should_tazza_declare_surprise_stop(
                player,
                self.state.discard_pile,
                self.state.round_number,
                self.state.players,
            ):
                return False

        elif (
            player.ai_difficulty
            == AIDifficulty.ADVANCED
            and not should_advanced_declare_surprise_stop(
                player,
                self.state.discard_pile,
            )
        ):
            return False

        self.declare_surprise_stop(
            player_id
        )

        return True


    def play_beginner_ai_turn(
        self,
        player_id: str,
    ):
        """
        초보 AI의 현재 턴을 진행한다.

        일반 턴:
            DRAW
            → 기습 STOP 확인
            → 카드 1장 드로우
            → DISCARD
            → 일반 STOP 확인
            → 버릴 카드 선택
            → 실제 버리기
            → 바가지 자동 선언 확인
            → REACTION

        선의 첫 턴:
            이미 DISCARD 상태이므로
            드로우 없이
            일반 STOP 확인 후 바로 버린다.

        반환값:
            AI가 실제로 버린 Card
            또는 라운드 종료 시 None
        """
        if self.state.status != GameStatus.PLAYING:
            raise ValueError(
                "현재는 진행 중인 라운드가 아닙니다."
            )

        if (
            self.state.current_turn_player_id
            != player_id
        ):
            raise ValueError(
                "현재 턴 플레이어가 아닙니다."
            )

        player = None

        for target in self.state.players:
            if target.player_id == player_id:
                player = target
                break

        if player is None:
            raise ValueError(
                f"플레이어를 찾을 수 없습니다: "
                f"{player_id}"
            )

        if player.player_type != PlayerType.BOT:
            raise ValueError(
                "AI 플레이어만 사용할 수 있습니다."
            )

        if (
            player.ai_difficulty
            not in (
                AIDifficulty.BEGINNER,
                AIDifficulty.INTERMEDIATE,
                AIDifficulty.ADVANCED,
                AIDifficulty.TAZZA,
            )
        ):
            raise ValueError(
                "현재 함수는 초보/중수/고수/타짜 AI 전용입니다."
            )

        # ---------------------------------
        # 일반 턴 시작:
        # 드로우 전에 기습 STOP부터 확인
        # ---------------------------------
        if self.state.turn_phase == TurnPhase.DRAW:
            surprise_stop_declared = (
                self.try_beginner_ai_surprise_stop(
                    player_id
                )
            )

            if surprise_stop_declared:
                return None

            drawn_card = self.draw_card()

            # 덱 소진으로 라운드가 끝났다면
            # 더 이상 진행하지 않는다.
            if drawn_card is None:
                return None

        # ---------------------------------
        # 드로우 후 또는 선 첫 턴:
        # 일반 STOP 확인
        # ---------------------------------
        stop_declared = (
            self.try_beginner_ai_stop(
                player_id
            )
        )

        if stop_declared:
            return None

        if self.state.turn_phase != TurnPhase.DISCARD:
            raise ValueError(
                "AI가 카드를 버릴 수 있는 "
                "상태가 아닙니다."
            )

        # play_beginner_ai_discard() 내부에서
        # 버린 뒤 바가지 조건도 자동 검사한다.
        discarded_card = (
            self.play_beginner_ai_discard(
                player_id
            )
        )

        return discarded_card

    def try_beginner_ai_bagaji(
        self,
        player_id: str,
    ) -> bool:
        """
        초보 AI가 현재 손패로 바가지를 선언할 수 있으면
        실제로 하나 선언한다.

        우선순위:
        1. 폭탄 바가지
        2. 일반 바가지

        이미 활성 바가지가 있으면 아무것도 하지 않는다.
        """
        if self.state.status != GameStatus.PLAYING:
            return False

        player = next(
            (
                player
                for player in self.state.players
                if player.player_id == player_id
            ),
            None,
        )

        if player is None:
            raise ValueError(
                f"플레이어를 찾을 수 없습니다: "
                f"{player_id}"
            )

        if player.player_type != PlayerType.BOT:
            return False

        if (
            player.ai_difficulty
            not in (
                AIDifficulty.BEGINNER,
                AIDifficulty.INTERMEDIATE,
                AIDifficulty.ADVANCED,
                AIDifficulty.TAZZA,
            )
        ):
            return False

        # 이미 일반/폭탄 바가지 중 하나라도
        # 활성 상태라면 추가 선언하지 않는다.
        if self._player_has_active_bagaji(
            player_id
        ):
            return False

        # ---------------------------------
        # 1. 폭탄 바가지 우선
        # ---------------------------------

        if (
            player.ai_difficulty
            == AIDifficulty.TAZZA
        ):
            bomb_bagaji_month = (
                choose_tazza_bomb_bagaji_month(
                    player,
                    self.state.discard_pile,
                    self.state.round_number,
                    self.state.players,
                )
            )
        elif (
            player.ai_difficulty
            == AIDifficulty.ADVANCED
        ):
            bomb_bagaji_month = (
                choose_advanced_bomb_bagaji_month(
                    player,
                    self.state.discard_pile,
                )
            )
        else:
            bomb_bagaji_month = (
                choose_beginner_bomb_bagaji_month(
                    player
                )
            )

        if bomb_bagaji_month is not None:
            self.declare_bomb_bagaji(
                player_id=player_id,
                month=bomb_bagaji_month,
            )

            return True

        # ---------------------------------
        # 2. 일반 바가지
        # ---------------------------------

        if (
            player.ai_difficulty
            == AIDifficulty.TAZZA
        ):
            general_bagaji_month = (
                choose_tazza_general_bagaji_month(
                    player,
                    self.state.discard_pile,
                    self.state.round_number,
                    self.state.players,
                )
            )
        elif (
            player.ai_difficulty
            == AIDifficulty.ADVANCED
        ):
            general_bagaji_month = (
                choose_advanced_general_bagaji_month(
                    player,
                    self.state.discard_pile,
                )
            )
        else:
            general_bagaji_month = (
                choose_beginner_general_bagaji_month(
                    player
                )
            )

        if general_bagaji_month is not None:
            self.declare_general_bagaji(
                player_id=player_id,
                month=general_bagaji_month,
            )

            return True

        return False


    def try_beginner_ai_bbung(
        self,
        player_id: str,
    ) -> bool:
        """
        초보 AI가 현재 마지막 버림패에
        뻥할 수 있으면 실제로 선언한다.

        반환값:
            True:
                뻥 실행

            False:
                뻥하지 않음
        """
        if self.state.status != GameStatus.PLAYING:
            return False

        if self.state.turn_phase != TurnPhase.REACTION:
            return False

        if not self.can_player_declare_bbung(
            player_id
        ):
            return False

        player = None

        for target in self.state.players:
            if target.player_id == player_id:
                player = target
                break

        if player is None:
            raise ValueError(
                f"플레이어를 찾을 수 없습니다: "
                f"{player_id}"
            )

        if player.player_type != PlayerType.BOT:
            raise ValueError(
                "AI 플레이어만 사용할 수 있습니다."
            )

        if (
            player.ai_difficulty
            not in (
                AIDifficulty.BEGINNER,
                AIDifficulty.INTERMEDIATE,
                AIDifficulty.ADVANCED,
                AIDifficulty.TAZZA,
            )
        ):
            raise ValueError(
                "현재 함수는 초보/중수/고수/타짜 AI 전용입니다."
            )

        discarded_card = (
            self.state.last_discarded_card
        )

        if discarded_card is None:
            return False

        if (
            player.ai_difficulty
            == AIDifficulty.TAZZA
        ):
            selection = (
                choose_tazza_bbung_cards(
                    player,
                    discarded_card,
                    self.state.discard_pile,
                )
            )
        elif (
            player.ai_difficulty
            == AIDifficulty.ADVANCED
        ):
            selection = (
                choose_advanced_bbung_cards(
                    player,
                    discarded_card,
                    self.state.discard_pile,
                )
            )
        else:
            selection = (
                choose_beginner_bbung_cards(
                    player,
                    discarded_card,
                )
            )

        if selection is None:
            return False

        matching_cards, extra_card = selection

        self.declare_bbung(
            player_id=player.player_id,
            matching_card_ids=[
                card.card_id
                for card in matching_cards
            ],
            extra_discard_card_id=(
                extra_card.card_id
            ),
        )

        # 뻥으로 실제 손패가 변경된 뒤
        # 남은 패가 바가지 조건을 만족하면
        # 초보 AI가 즉시 바가지를 선언한다.
        self.try_beginner_ai_bagaji(
            player.player_id
        )

        return True

    def process_beginner_ai_bbung_reaction(
        self,
    ) -> bool:
        """
        현재 REACTION 단계에서
        뻥 가능한 플레이어가 초보 AI라면
        자동으로 뻥을 실행한다.

        정상적인 카드 구성에서는
        뻥 후보가 0명 또는 1명만 존재할 수 있다.

        반환값:
            True:
                초보 AI가 실제로 뻥함

            False:
                뻥 후보가 없거나
                후보가 사람이거나
                초보 AI가 아님
        """
        if self.state.status != GameStatus.PLAYING:
            return False

        if self.state.turn_phase != TurnPhase.REACTION:
            return False

        candidate_ids = (
            self.state.bbung_candidate_player_ids
        )

        if not candidate_ids:
            return False

        if len(candidate_ids) > 1:
            raise ValueError(
                "카드 구성상 뻥 후보가 "
                "2명 이상일 수 없습니다."
            )

        candidate_id = candidate_ids[0]

        player = None

        for target in self.state.players:
            if target.player_id == candidate_id:
                player = target
                break

        if player is None:
            raise ValueError(
                f"플레이어를 찾을 수 없습니다: "
                f"{candidate_id}"
            )

        if player.player_type != PlayerType.BOT:
            return False

        if (
            player.ai_difficulty
            not in (
                AIDifficulty.BEGINNER,
                AIDifficulty.INTERMEDIATE,
                AIDifficulty.ADVANCED,
                AIDifficulty.TAZZA,
            )
        ):
            return False

        return self.try_beginner_ai_bbung(
            candidate_id
        )

    def process_all_beginner_ai_bbung_reactions(
        self,
    ) -> int:
        """
        초보 AI의 연속 뻥 반응을
        가능한 만큼 자동으로 처리한다.

        예:
            P1이 3월 버림
            → P2가 3월 뻥 후 9월 버림
            → P3가 9월 뻥 후 6월 버림

        반환값:
            실제로 발생한 자동 뻥 횟수
        """
        bbung_count = 0

        while (
            self.state.status == GameStatus.PLAYING
            and self.state.turn_phase
            == TurnPhase.REACTION
        ):
            processed = (
                self.process_beginner_ai_bbung_reaction()
            )

            if not processed:
                break

            bbung_count += 1

        return bbung_count


    def resolve_beginner_ai_reaction_flow(
        self,
    ) -> int:
        """
        초보 AI의 뻥 반응을 가능한 만큼 처리한 뒤,
        더 이상 뻥 후보가 없으면 반응 단계를 종료하고
        다음 플레이어의 턴으로 진행한다.

        사람이 뻥 후보인 경우에는
        사람이 선택해야 하므로 REACTION 상태를 유지한다.

        반환값:
            이번 처리에서 발생한 AI 뻥 횟수
        """
        bbung_count = (
            self.process_all_beginner_ai_bbung_reactions()
        )

        if self.state.status != GameStatus.PLAYING:
            return bbung_count

        if self.state.turn_phase != TurnPhase.REACTION:
            return bbung_count

        candidate_ids = (
            self.state.bbung_candidate_player_ids
        )

        if len(candidate_ids) > 1:
            raise ValueError(
                "카드 구성상 뻥 후보가 "
                "2명 이상일 수 없습니다."
            )

        # 후보가 남아 있다면
        # 사람 플레이어 등이 직접 반응해야 한다.
        if candidate_ids:
            return bbung_count

        # 아무도 뻥할 수 없다면
        # 반응창을 닫고 다음 턴으로 이동한다.
        if self.state.bbung_reaction_open:
            self.close_bbung_reaction_window()

        self.advance_turn()

        return bbung_count


    def run_beginner_ai_until_human_turn(
        self,
    ) -> int:
        """
        현재 차례부터 초보 AI들의 턴을
        사람이 나올 때까지 자동으로 진행한다.

        반환값:
            자동으로 처리한 AI 턴 수
        """
        ai_turn_count = 0

        while self.state.status == GameStatus.PLAYING:
            current_player = self.get_current_player()

            # 사람 차례가 오면 자동 진행 중단
            if current_player.player_type == PlayerType.HUMAN:
                break

            # 현재는 초보/중수/고수/타짜 AI를 자동 진행
            if (
                current_player.ai_difficulty
                not in (
                    AIDifficulty.BEGINNER,
                    AIDifficulty.INTERMEDIATE,
                    AIDifficulty.ADVANCED,
                    AIDifficulty.TAZZA,
                )
            ):
                break

            # AI 턴 시작
            if self.state.turn_phase in (
                TurnPhase.DRAW,
                TurnPhase.DISCARD,
            ):
                self.play_beginner_ai_turn(
                    current_player.player_id
                )

                ai_turn_count += 1

            # STOP 등으로 라운드가 끝났다면 종료
            if self.state.status != GameStatus.PLAYING:
                break

            # 카드 버린 뒤 REACTION 처리
            if self.state.turn_phase == TurnPhase.REACTION:
                self.resolve_beginner_ai_reaction_flow()

            # 반응 처리 후에도 아직
            # 사람이 반응해야 하는 상황이면 중단
            if self.state.turn_phase == TurnPhase.REACTION:
                break

        return ai_turn_count


    def try_beginner_ai_stop(
        self,
        player_id: str,
    ) -> bool:
        """
        초보 AI가 현재 STOP 가능 여부를 확인하고,
        가능하면 첫 번째 STOP을 즉시 선언한다.

        반환값:
            True:
                STOP 선언으로 라운드 종료

            False:
                선언 가능한 STOP 없음
        """
        if self.state.status != GameStatus.PLAYING:
            return False

        if (
            self.state.current_turn_player_id
            != player_id
        ):
            return False

        if self.state.turn_phase != TurnPhase.DISCARD:
            return False

        player = None

        for target in self.state.players:
            if target.player_id == player_id:
                player = target
                break

        if player is None:
            raise ValueError(
                f"플레이어를 찾을 수 없습니다: "
                f"{player_id}"
            )

        if player.player_type != PlayerType.BOT:
            raise ValueError(
                "AI 플레이어만 사용할 수 있습니다."
            )

        if (
            player.ai_difficulty
            not in (
                AIDifficulty.BEGINNER,
                AIDifficulty.INTERMEDIATE,
                AIDifficulty.ADVANCED,
                AIDifficulty.TAZZA,
            )
        ):
            raise ValueError(
                "현재 함수는 초보/중수/고수/타짜 AI 전용입니다."
            )

        available_stops = (
            self.get_current_player_stops()
        )

        if not available_stops:
            return False

        if (
            player.ai_difficulty
            == AIDifficulty.TAZZA
        ):
            selected_stop = (
                choose_tazza_stop(
                    player,
                    available_stops,
                    calculate_stop_score,
                    self.state.round_number,
                    self.state.players,
                )
            )

            if selected_stop is None:
                return False

        elif (
            player.ai_difficulty
            == AIDifficulty.ADVANCED
        ):
            selected_stop = (
                choose_advanced_stop(
                    player,
                    available_stops,
                    calculate_stop_score,
                )
            )
        else:
            selected_stop = (
                available_stops[0]
            )

        self.declare_stop(
            selected_stop
        )

        return True
