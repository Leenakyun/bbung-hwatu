let currentGameId = null;
        let currentGameMode = null;
        let currentPlayerId = null;

        let authToken =
            sessionStorage.getItem(
                "bbung-auth-token"
            )
            || null;

        let currentAuthUser = null;

        const onlineClientId =
            sessionStorage.getItem(
                "bbung-online-client-id"
            )
            || (
                (
                    window.crypto
                    && crypto.randomUUID
                )
                ? crypto.randomUUID()
                : (
                    "CLIENT-"
                    + Date.now()
                    + "-"
                    + Math.random()
                        .toString(36)
                        .slice(2)
                )
            );

        sessionStorage.setItem(
            "bbung-online-client-id",
            onlineClientId
        );

        let onlineJoinInFlight = false;
        let currentOwnerId = null;
        let realtimeSocket = null;
        let realtimeReconnectTimer = null;

        let selectedBbungExtraCardId =
            null;

        let currentBbungMatchingCardIds =
            [];

        const authUsername =
            document.getElementById(
                "authUsername"
            );

        const authPassword =
            document.getElementById(
                "authPassword"
            );

        const authNickname =
            document.getElementById(
                "authNickname"
            );

        const authStatus =
            document.getElementById(
                "authStatus"
            );

        const registerButton =
            document.getElementById(
                "registerButton"
            );

        const loginButton =
            document.getElementById(
                "loginButton"
            );

        const logoutButton =
            document.getElementById(
                "logoutButton"
            );

        const aiDifficultySelect =
            document.getElementById(
                "aiDifficultySelect"
            );

        const onlineNickname =
            document.getElementById(
                "onlineNickname"
            );

        const onlineMaxPlayers =
            document.getElementById(
                "onlineMaxPlayers"
            );

        const onlineRoomId =
            document.getElementById(
                "onlineRoomId"
            );

        const roomCreateModal =
            document.getElementById(
                "roomCreateModal"
            );

        const roomShareModal =
            document.getElementById(
                "roomShareModal"
            );

        const roomJoinModal =
            document.getElementById(
                "roomJoinModal"
            );

        const rulesModal =
            document.getElementById(
                "rulesModal"
            );

        const roomPasswordCreateWrap =
            document.getElementById(
                "roomPasswordCreateWrap"
            );

        const roomPasswordCreate =
            document.getElementById(
                "roomPasswordCreate"
            );

        const joinRoomId =
            document.getElementById(
                "joinRoomId"
            );

        const roomPasswordJoin =
            document.getElementById(
                "roomPasswordJoin"
            );

        const inviteLinkInput =
            document.getElementById(
                "inviteLinkInput"
            );

        const createdRoomSummary =
            document.getElementById(
                "createdRoomSummary"
            );

        const dealerSelectionPanel =
            document.getElementById(
                "dealerSelectionPanel"
            );

        const dealerSelectionMode =
            document.getElementById(
                "dealerSelectionMode"
            );

        const dealerSelectionHistory =
            document.getElementById(
                "dealerSelectionHistory"
            );

        const dealerDrawButton =
            document.getElementById(
                "dealerDrawButton"
            );

        const confirmOnlineStartButton =
            document.getElementById(
                "confirmOnlineStartButton"
            );

        const realtimeStatus =
            document.getElementById(
                "realtimeStatus"
            );

        const onlinePlayerId =
            document.getElementById(
                "onlinePlayerId"
            );

        const gameStatusElement =
            document.getElementById(
                "gameStatus"
            );

        const myHandElement =
            document.getElementById(
                "myHand"
            );

        const nextRoundPanel =
            document.getElementById(
                "nextRoundPanel"
            );

        const nextRoundButton =
            document.getElementById(
                "nextRoundButton"
            );

        const tieBreakPanel =
            document.getElementById(
                "tieBreakPanel"
            );

        const tieBreakInfo =
            document.getElementById(
                "tieBreakInfo"
            );

        const tieBreakDrawButton =
            document.getElementById(
                "tieBreakDrawButton"
            );

        const roundResultPanel =
            document.getElementById(
                "roundResultPanel"
            );

        const roundResultElement =
            document.getElementById(
                "roundResult"
            );

        const playersElement =
            document.getElementById(
                "players"
            );

        const discardPileElement =
            document.getElementById(
                "discardPile"
            );

        const messageElement =
            document.getElementById(
                "message"
            );

        const drawDeck =
            document.getElementById(
                "drawDeck"
            );

        const stopPanel =
            document.getElementById(
                "stopPanel"
            );

        const stopCallButton =
            document.getElementById(
                "stopCallButton"
            );

        const stopButtons =
            document.getElementById(
                "stopButtons"
            );

        const surpriseStopPanel =
            document.getElementById(
                "surpriseStopPanel"
            );

        const surpriseStopButton =
            document.getElementById(
                "surpriseStopButton"
            );

        const bombBagajiPanel =
            document.getElementById(
                "bombBagajiPanel"
            );

        const bombBagajiStatus =
            document.getElementById(
                "bombBagajiStatus"
            );

        const bombBagajiCallButton =
            document.getElementById(
                "bombBagajiCallButton"
            );


        const generalBagajiPanel =
            document.getElementById(
                "generalBagajiPanel"
            );

        const generalBagajiStatus =
            document.getElementById(
                "generalBagajiStatus"
            );

        const generalBagajiCallButton =
            document.getElementById(
                "generalBagajiCallButton"
            );

        const bbungPanel =
            document.getElementById(
                "bbungPanel"
            );

        const bbungMessage =
            document.getElementById(
                "bbungMessage"
            );

        const bbungExtraCards =
            document.getElementById(
                "bbungExtraCards"
            );

        const bbungConfirmButton =
            document.getElementById(
                "bbungConfirmButton"
            );

        const bbungPassButton =
            document.getElementById(
                "bbungPassButton"
            );

        const authView = document.getElementById("authView");
        const lobbyView = document.getElementById("lobbyView");
        const gameView = document.getElementById("gameView");
        const lobbyWelcome = document.getElementById("lobbyWelcome");
        const publicRoomsList = document.getElementById("publicRoomsList");
        const publicRoomsEmpty = document.getElementById("publicRoomsEmpty");
        const refreshPublicRoomsButton = document.getElementById("refreshPublicRoomsButton");
        const homeButton = document.getElementById("homeButton");
        const backToLobbyButton = document.getElementById("backToLobbyButton");
        const musicToggle = document.getElementById("musicToggle");
        const soundToggle = document.getElementById("soundToggle");
        const declarationStatusBadge = document.getElementById("declarationStatusBadge");
        const lobbyBgm = document.getElementById("lobbyBgm");
        const gameBgm = document.getElementById("gameBgm");

        let musicEnabled = false;
        let soundEnabled = true;
        let toastTimer = null;
        let lastResultSoundKey = null;

        const soundEffects = {
            draw: new Audio("/assets/sfx/draw.wav"),
            discard: new Audio("/assets/sfx/discard.wav"),
            bbung: new Audio("/assets/sfx/bbung.wav"),
            bagaji: new Audio("/assets/sfx/bagaji.wav"),
            bomb: new Audio("/assets/sfx/bomb.wav"),
            win: new Audio("/assets/sfx/win.wav"),
        };


        const nativeFetch =
            window.fetch.bind(
                window
            );


        function cardImagePath(card) {
            if (!card) {
                return "";
            }

            const parts =
                (card.card_id || "")
                    .split("-");

            if (parts.length === 2) {
                const month = Number(parts[0]);
                const copy = Number(parts[1]);

                if (month && copy) {
                    return `/assets/cards/${month}_${copy}.png`;
                }
            }

            if (card.month && card.copy_index) {
                return `/assets/cards/${card.month}_${card.copy_index}.png`;
            }

            return "";
        }


        function cardMarkup(card) {
            const imagePath = cardImagePath(card);

            if (imagePath) {
                return `
                    <img src="${imagePath}" alt="${card.month}월 화투패" loading="eager">
                    <span class="card-month">${card.month}월</span>
                    <span class="card-id">${card.card_id || ""}</span>
                `;
            }

            return `
                <span class="card-month">${card.month}월</span>
                <span class="card-id">${card.card_id || ""}</span>
            `;
        }


        function playEffect(name) {
            if (!soundEnabled) {
                return;
            }

            const audio = soundEffects[name];
            if (!audio) {
                return;
            }

            try {
                audio.currentTime = 0;
                audio.play().catch(() => {});
            } catch (_error) {
                // 오디오 재생 실패는 게임 진행에 영향 없음.
            }
        }


        function playElderlyAigo() {
            if (!soundEnabled || !("speechSynthesis" in window)) {
                return;
            }

            const utterance = new SpeechSynthesisUtterance("아이고...");
            utterance.lang = "ko-KR";
            utterance.rate = 0.72;
            utterance.pitch = 0.78;
            utterance.volume = 1;

            const voices = window.speechSynthesis.getVoices();
            const koreanVoices = voices.filter(
                voice => (voice.lang || "").toLowerCase().startsWith("ko")
            );
            const preferred = koreanVoices.find(voice =>
                /female|woman|yuna|sora|sunhi|유나|소라|선희/i.test(voice.name || "")
            ) || koreanVoices[0];

            if (preferred) {
                utterance.voice = preferred;
            }

            window.speechSynthesis.cancel();
            window.speechSynthesis.speak(utterance);
        }


        function setUiMode(mode) {
            const isAuth = mode === "auth";
            const isLobby = mode === "lobby";
            const isGame = mode === "game";

            authView.hidden = !isAuth;
            lobbyView.hidden = !isLobby;
            gameView.hidden = !isGame;

            document.body.classList.toggle("game-mode", isGame);
            document.body.classList.toggle("lobby-mode", isLobby || isAuth);
            document.body.classList.toggle("auth-mode", isAuth);

            if (musicEnabled) {
                const active = isGame ? gameBgm : lobbyBgm;
                const inactive = isGame ? lobbyBgm : gameBgm;

                inactive.pause();
                active.volume = 0.22;
                active.play().catch(() => {});
            }
        }


        function buildHeaders(
            initialHeaders
        ) {
            const headers =
                new Headers(
                    initialHeaders || {}
                );

            if (authToken) {
                headers.set(
                    "Authorization",
                    `Bearer ${authToken}`
                );
            }

            if (
                currentGameMode
                === "ONLINE"
                && currentPlayerId
            ) {
                headers.set(
                    "X-Player-ID",
                    currentPlayerId
                );
            }

            return headers;
        }


        function apiFetch(
            input,
            options = {}
        ) {
            return nativeFetch(
                input,
                {
                    ...options,
                    headers:
                        buildHeaders(
                            options.headers
                        ),
                }
            );
        }


        function renderAuthStatus() {
            if (currentAuthUser) {
                authStatus.textContent =
                    `로그인: `
                    + `${currentAuthUser.nickname} `
                    + `(${currentAuthUser.username})`;

                if (
                    !onlineNickname.value
                    || onlineNickname.value
                        === "플레이어"
                ) {
                    onlineNickname.value =
                        currentAuthUser.nickname;
                }

                if (lobbyWelcome) {
                    lobbyWelcome.textContent =
                        `${currentAuthUser.nickname}님의 로비`;
                }

                return;
            }

            authStatus.textContent =
                "로그인 안 됨";
        }


        async function refreshAuth() {
            if (!authToken) {
                currentAuthUser = null;
                renderAuthStatus();
                setUiMode("auth");
                return;
            }

            try {
                const response =
                    await apiFetch(
                        "/api/auth/me",
                        {
                            cache: "no-store",
                        }
                    );

                const data =
                    await response.json();

                if (!response.ok) {
                    authToken = null;
                    currentAuthUser = null;

                    sessionStorage.removeItem(
                        "bbung-auth-token"
                    );

                    renderAuthStatus();
                    setUiMode("auth");
                    return;
                }

                currentAuthUser =
                    data.user;

                renderAuthStatus();
                setUiMode(authToken ? "lobby" : "auth");
                await refreshPublicRooms();

            } catch (_error) {
                currentAuthUser = null;
                renderAuthStatus();
                setUiMode("auth");
            }
        }


        async function registerAccount() {
            const username =
                authUsername.value.trim();

            const password =
                authPassword.value;

            const nickname =
                authNickname.value.trim();

            try {
                const response =
                    await nativeFetch(
                        "/api/auth/register",
                        {
                            method: "POST",
                            headers: {
                                "Content-Type":
                                    "application/json",
                            },
                            body: JSON.stringify(
                                {
                                    username,
                                    password,
                                    nickname,
                                }
                            ),
                        }
                    );

                const data =
                    await response.json();

                if (!response.ok) {
                    showMessage(
                        data.message
                        || "회원가입 실패"
                    );
                    return;
                }

                showMessage(
                    "회원가입 완료. "
                    + "이제 로그인해 주세요."
                );

            } catch (error) {
                showMessage(
                    `회원가입 오류: ${error}`
                );
            }
        }


        async function loginAccount() {
            const username =
                authUsername.value.trim();

            const password =
                authPassword.value;

            try {
                const response =
                    await nativeFetch(
                        "/api/auth/login",
                        {
                            method: "POST",
                            headers: {
                                "Content-Type":
                                    "application/json",
                            },
                            body: JSON.stringify(
                                {
                                    username,
                                    password,
                                }
                            ),
                        }
                    );

                const data =
                    await response.json();

                if (!response.ok) {
                    showMessage(
                        data.message
                        || "로그인 실패"
                    );
                    return;
                }

                authToken = data.token;
                currentAuthUser =
                    data.user;

                sessionStorage.setItem(
                    "bbung-auth-token",
                    authToken
                );

                renderAuthStatus();

                onlineNickname.value =
                    currentAuthUser.nickname;

                setUiMode("lobby");
                await refreshPublicRooms();

                if (typeof invitedRoomId !== "undefined" && invitedRoomId) {
                    onlineRoomId.value = invitedRoomId;
                    joinRoomId.value = invitedRoomId;
                    openModal(roomJoinModal);
                }

                showMessage(
                    `${currentAuthUser.nickname}`
                    + " 로그인 완료"
                );

            } catch (error) {
                showMessage(
                    `로그인 오류: ${error}`
                );
            }
        }


        async function logoutAccount() {
            try {
                if (authToken) {
                    await apiFetch(
                        "/api/auth/logout",
                        {
                            method: "POST",
                        }
                    );
                }
            } finally {
                authToken = null;
                currentAuthUser = null;

                sessionStorage.removeItem(
                    "bbung-auth-token"
                );

                closeRealtime();

                currentGameId = null;
                currentGameMode = null;
                currentPlayerId = null;
                currentOwnerId = null;

                onlinePlayerId.textContent =
                    "없음";

                renderAuthStatus();
                setUiMode("auth");

                showMessage(
                    "로그아웃했습니다."
                );
            }
        }


        function publicRoomStatusLabel(room) {
            if (room.status === "WAITING") {
                return room.is_full ? "꽉 참" : "대기 중";
            }
            if (room.status === "DEALER_SELECTION") {
                return "선 정하는 중";
            }
            if (room.status === "PLAYING") {
                return "게임 중";
            }
            if (room.status === "ROUND_END") {
                return "라운드 정산 중";
            }
            if (room.status === "TIE_BREAK") {
                return "순위 결정 중";
            }
            if (room.status === "GAME_END") {
                return "게임 종료";
            }
            return room.status || "상태 확인 중";
        }


        function renderPublicRooms(rooms) {
            if (!publicRoomsList || !publicRoomsEmpty) {
                return;
            }

            publicRoomsList.replaceChildren();
            const roomItems = Array.isArray(rooms) ? rooms : [];
            publicRoomsEmpty.hidden = roomItems.length > 0;

            roomItems.forEach(room => {
                const row = document.createElement("div");
                row.className = "public-room-row";

                const main = document.createElement("div");
                main.className = "public-room-main";
                const title = document.createElement("strong");
                title.textContent = room.game_id;
                const owner = document.createElement("small");
                owner.textContent = `방장 ${room.owner_nickname || "-"}`;
                main.append(title, owner);

                const count = document.createElement("span");
                count.className = "public-room-count";
                count.textContent = `${room.player_count}/${room.max_players}명`;

                const status = document.createElement("span");
                status.className = "public-room-status " + (room.can_join ? "waiting" : "playing");
                status.textContent = publicRoomStatusLabel(room);

                const join = document.createElement("button");
                join.type = "button";
                join.className = "ghost-button public-room-join";
                join.textContent = room.can_join ? "입장" : "입장 불가";
                join.disabled = !room.can_join;
                join.addEventListener("click", () => {
                    onlineRoomId.value = room.game_id;
                    joinRoomId.value = room.game_id;
                    roomPasswordJoin.value = "";
                    openModal(roomJoinModal);
                });

                row.append(main, count, status, join);
                publicRoomsList.append(row);
            });
        }


        async function refreshPublicRooms() {
            if (!authToken) {
                renderPublicRooms([]);
                return;
            }

            try {
                if (refreshPublicRoomsButton) {
                    refreshPublicRoomsButton.disabled = true;
                }

                const response = await apiFetch(
                    "/api/online/rooms",
                    { cache: "no-store" }
                );
                const data = await response.json();

                if (!response.ok) {
                    throw new Error(data.message || "공개방 목록 조회 실패");
                }

                renderPublicRooms(data.rooms);
            } catch (_error) {
                renderPublicRooms([]);
            } finally {
                if (refreshPublicRoomsButton) {
                    refreshPublicRoomsButton.disabled = false;
                }
            }
        }


        function closeRealtime() {
            if (
                realtimeReconnectTimer
                !== null
            ) {
                clearTimeout(
                    realtimeReconnectTimer
                );
                realtimeReconnectTimer =
                    null;
            }

            if (realtimeSocket) {
                realtimeSocket.close();
                realtimeSocket = null;
            }

            realtimeStatus.textContent =
                "연결 안 됨";
        }


        function connectRealtime() {
            closeRealtime();

            if (
                currentGameMode
                !== "ONLINE"
                || !currentGameId
                || !currentPlayerId
                || !authToken
            ) {
                return;
            }

            const eventUrl =
                `/events/${currentGameId}`
                + `?player_id=`
                + encodeURIComponent(
                    currentPlayerId
                )
                + `&token=`
                + encodeURIComponent(
                    authToken
                );

            realtimeStatus.textContent =
                "연결 중";

            const source =
                new EventSource(
                    eventUrl
                );

            realtimeSocket =
                source;

            source.addEventListener(
                "open",
                () => {
                    if (
                        realtimeSocket
                        !== source
                    ) {
                        return;
                    }

                    realtimeStatus
                        .textContent =
                        "연결됨";
                }
            );

            source.addEventListener(
                "message",
                event => {
                    let payload = null;

                    try {
                        payload =
                            JSON.parse(
                                event.data
                            );
                    } catch (_error) {
                        return;
                    }

                    if (
                        payload.type
                        === "CONNECTED"
                    ) {
                        realtimeStatus
                            .textContent =
                            "연결됨";
                        return;
                    }

                    if (
                        payload.type
                        === "STATE_UPDATE"
                        && payload.game
                    ) {
                        renderGame(
                            payload.game
                        );
                    }

                    if (
                        payload.type
                        === "ERROR"
                    ) {
                        showMessage(
                            payload.error
                            || "실시간 연결 오류"
                        );
                    }
                }
            );

            source.addEventListener(
                "error",
                () => {
                    if (
                        realtimeSocket
                        !== source
                    ) {
                        return;
                    }

                    realtimeStatus
                        .textContent =
                        "재연결 중";
                }
            );
        }


        async function refreshAfterAction() {
            // ONLINE:
            // 성공한 POST 직후 서버가 SSE로
            // STATE_UPDATE를 전송하므로 중복 GET을 하지 않는다.
            //
            // SOLO_AI:
            // SSE를 사용하지 않으므로 기존처럼
            // REST로 최신 상태를 다시 조회한다.
            if (
                currentGameMode
                === "ONLINE"
            ) {
                return;
            }

            await refreshGame();
        }


        function openModal(modal) {
            if (!modal) {
                return;
            }

            modal.hidden = false;
            document.body.classList.add(
                "modal-open"
            );
        }


        function closeModal(modal) {
            if (!modal) {
                return;
            }

            modal.hidden = true;

            if (
                !document.querySelector(
                    ".modal-backdrop:not([hidden])"
                )
            ) {
                document.body.classList.remove(
                    "modal-open"
                );
            }
        }


        function getSelectedRoomPrivacy() {
            const selected =
                document.querySelector(
                    'input[name="roomPrivacy"]:checked'
                );

            return selected
                ? selected.value
                : "PUBLIC";
        }


        function normalizeRoomId(value) {
            const raw = String(
                value || ""
            ).trim();

            if (!raw) {
                return "";
            }

            try {
                const parsed = new URL(
                    raw,
                    window.location.href
                );
                const fromQuery =
                    parsed.searchParams.get(
                        "room"
                    );

                if (fromQuery) {
                    return fromQuery
                        .trim()
                        .toUpperCase();
                }
            } catch (_error) {
                // 일반 방 ID 입력이면 아래에서 그대로 처리한다.
            }

            return raw.toUpperCase();
        }


        function buildInviteLink(gameId) {
            const inviteUrl = new URL(
                window.location.href
            );

            inviteUrl.search = "";
            inviteUrl.hash = "";
            inviteUrl.searchParams.set(
                "room",
                gameId
            );

            return inviteUrl.toString();
        }


        function openCreateRoomModal() {
            if (!authToken) {
                showMessage(
                    "온라인 대전은 로그인이 필요합니다."
                );
                return;
            }

            roomPasswordCreate.value = "";
            roomPasswordCreateWrap.hidden =
                getSelectedRoomPrivacy()
                !== "PRIVATE";
            openModal(
                roomCreateModal
            );
        }


        function openJoinRoomModal() {
            if (!authToken) {
                showMessage(
                    "온라인 대전은 로그인이 필요합니다."
                );
                return;
            }

            const roomId = normalizeRoomId(
                onlineRoomId.value
            );

            if (!roomId) {
                showMessage(
                    "참가할 방 ID 또는 초대 링크를 입력해 주세요."
                );
                return;
            }

            joinRoomId.value = roomId;
            roomPasswordJoin.value = "";
            openModal(
                roomJoinModal
            );
        }


        async function copyInviteLink() {
            const link =
                inviteLinkInput.value;

            if (!link) {
                return;
            }

            try {
                await navigator.clipboard
                    .writeText(
                        link
                    );
            } catch (_error) {
                inviteLinkInput.select();
                document.execCommand(
                    "copy"
                );
            }

            showMessage(
                "초대 링크를 복사했습니다."
            );
        }


        function showMessage(message) {
            messageElement.textContent = message;
            messageElement.classList.add("is-visible");

            if (toastTimer !== null) {
                clearTimeout(toastTimer);
            }

            toastTimer = setTimeout(
                () => messageElement.classList.remove("is-visible"),
                3200
            );
        }


        async function createOnlineRoom() {
            try {
                const nickname =
                    onlineNickname.value
                        .trim()
                    || "방장";

                if (!authToken) {
                    showMessage(
                        "온라인 대전은 로그인이 필요합니다."
                    );
                    return;
                }

                const roomPrivacy =
                    getSelectedRoomPrivacy();

                const isPrivate =
                    roomPrivacy === "PRIVATE";

                const roomPassword =
                    roomPasswordCreate.value;

                if (
                    isPrivate
                    && roomPassword.length < 4
                ) {
                    showMessage(
                        "비밀방 비밀번호는 4자 이상 입력해 주세요."
                    );
                    return;
                }

                const response =
                    await apiFetch(
                        "/api/online/rooms",
                        {
                            method: "POST",
                            headers: {
                                "Content-Type":
                                    "application/json",
                            },
                            body: JSON.stringify(
                                {
                                    client_id:
                                        onlineClientId,
                                    nickname:
                                        nickname,
                                    max_players:
                                        Number(
                                            onlineMaxPlayers
                                                .value
                                        ),
                                    is_private:
                                        isPrivate,
                                    room_password:
                                        isPrivate
                                        ? roomPassword
                                        : "",
                                }
                            ),
                        }
                    );

                const data =
                    await response.json();

                if (!response.ok) {
                    showMessage(
                        data.message
                        || "온라인 방 생성 실패"
                    );
                    return;
                }

                currentGameId =
                    data.game_id;
                currentGameMode =
                    "ONLINE";
                currentPlayerId =
                    data.viewer_player_id;
                currentOwnerId =
                    data.owner_id;

                onlineRoomId.value =
                    currentGameId;

                onlinePlayerId.textContent =
                    currentPlayerId
                    || "없음";

                renderGame(
                    data
                );

                connectRealtime();

                closeModal(
                    roomCreateModal
                );

                inviteLinkInput.value =
                    buildInviteLink(
                        currentGameId
                    );

                createdRoomSummary.textContent =
                    `${currentGameId} · `
                    + `${data.max_players}인 · `
                    + (
                        data.is_private
                        ? "비밀방"
                        : "공개방"
                    );

                openModal(
                    roomShareModal
                );

                await refreshPublicRooms();

                showMessage(
                    `온라인 방 생성: `
                    + `${currentGameId}\n`
                    + `현재 인원: `
                    + `${data.players.length}/`
                    + `${data.max_players}`
                );

            } catch (error) {
                showMessage(
                    `온라인 방 생성 오류: `
                    + `${error}`
                );
            }
        }


        async function joinOnlineRoom() {
            if (!authToken) {
                showMessage(
                    "온라인 대전은 로그인이 필요합니다."
                );
                return;
            }

            if (onlineJoinInFlight) {
                return;
            }

            const roomId =
                normalizeRoomId(
                    joinRoomId.value
                    || onlineRoomId.value
                );

            if (!roomId) {
                showMessage(
                    "참가할 방 ID를 입력해 주세요."
                );
                return;
            }

            onlineJoinInFlight = true;

            try {
                const nickname =
                    onlineNickname.value
                        .trim()
                    || "플레이어";

                const response =
                    await apiFetch(
                        `/api/online/rooms/`
                        + `${roomId}/join`,
                        {
                            method: "POST",
                            headers: {
                                "Content-Type":
                                    "application/json",
                            },
                            body: JSON.stringify(
                                {
                                    nickname:
                                        nickname,
                                    client_id:
                                        onlineClientId,
                                    room_password:
                                        roomPasswordJoin
                                            .value,
                                }
                            ),
                        }
                    );

                const data =
                    await response.json();

                if (!response.ok) {
                    showMessage(
                        data.message
                        || "온라인 방 참가 실패"
                    );
                    return;
                }

                currentGameId =
                    data.game_id;
                currentGameMode =
                    "ONLINE";
                currentOwnerId = null;
                currentPlayerId =
                    data.viewer_player_id;

                onlineRoomId.value =
                    currentGameId;

                onlinePlayerId.textContent =
                    currentPlayerId
                    || "없음";

                closeModal(
                    roomJoinModal
                );

                renderGame(
                    data
                );

                connectRealtime();

                showMessage(
                    `온라인 방 참가: `
                    + `${currentGameId}\n`
                    + `내 ID: `
                    + `${currentPlayerId}`
                );

            } catch (error) {
                showMessage(
                    `온라인 방 참가 오류: `
                    + `${error}`
                );
            } finally {
                onlineJoinInFlight = false;
            }
        }


        async function startOnlineRoom() {
            if (
                currentGameMode
                !== "ONLINE"
                || !currentGameId
            ) {
                showMessage(
                    "온라인 방에 먼저 들어가 주세요."
                );
                return;
            }

            if (!currentOwnerId) {
                showMessage(
                    "방장만 게임을 시작할 수 있습니다."
                );
                return;
            }

            try {
                const response =
                    await apiFetch(
                        `/api/online/rooms/`
                        + `${currentGameId}/start`,
                        {
                            method: "POST",
                            headers: {
                                "Content-Type":
                                    "application/json",
                            },
                            body: JSON.stringify(
                                {
                                    owner_id:
                                        currentOwnerId,
                                }
                            ),
                        }
                    );

                const data =
                    await response.json();

                if (!response.ok) {
                    showMessage(
                        data.message
                        || "온라인 게임 시작 실패"
                    );
                    return;
                }

                renderGame(
                    data
                );

                showMessage(
                    "밤일낮짱을 시작합니다.\n"
                    + "각자 자신의 선 정하기 카드를 뽑아 주세요."
                );

            } catch (error) {
                showMessage(
                    `온라인 시작 오류: `
                    + `${error}`
                );
            }
        }


        async function drawDealerSelectionCard() {
            if (
                !currentGameId
                || !currentPlayerId
                || !["ONLINE", "SOLO_AI"].includes(currentGameMode)
            ) {
                return;
            }

            try {
                const dealerDrawUrl =
                    currentGameMode === "ONLINE"
                        ? `/api/online/rooms/${currentGameId}/dealer-selection/draw`
                        : `/api/games/${currentGameId}/dealer-selection/draw`;

                const response = await apiFetch(
                    dealerDrawUrl,
                    { method: "POST" }
                );
                const data = await response.json();

                if (!response.ok) {
                    showMessage(
                        data.message
                        || "선 정하기 카드 뽑기 실패"
                    );
                    return;
                }

                if (data.drawn_dealer_card) {
                    playEffect("draw");
                    showMessage(
                        `밤일낮짱: ${data.drawn_dealer_card.month}월을 뽑았습니다.`
                    );
                }

                renderGame(data);

                if (
                    currentGameMode === "SOLO_AI"
                    && data.status === "PLAYING"
                    && data.current_turn_player_id
                    && data.current_turn_player_id !== currentPlayerId
                ) {
                    await continueGame();
                }
            } catch (error) {
                showMessage(
                    `선 정하기 카드 뽑기 오류: ${error}`
                );
            }
        }


        async function confirmOnlineGameStart() {
            if (
                currentGameMode
                !== "ONLINE"
                || !currentGameId
                || !currentOwnerId
            ) {
                return;
            }

            try {
                const response =
                    await apiFetch(
                        `/api/online/rooms/`
                        + `${currentGameId}`
                        + `/confirm-start`,
                        {
                            method: "POST",
                            headers: {
                                "Content-Type":
                                    "application/json",
                            },
                            body: JSON.stringify(
                                {
                                    owner_id:
                                        currentOwnerId,
                                }
                            ),
                        }
                    );

                const data =
                    await response.json();

                if (!response.ok) {
                    showMessage(
                        data.message
                        || "본게임 시작 실패"
                    );
                    return;
                }

                renderGame(
                    data
                );

                showMessage(
                    `본게임 시작!\\n`
                    + `선: ${data.dealer_id}`
                );

            } catch (error) {
                showMessage(
                    `본게임 시작 오류: ${error}`
                );
            }
        }


        async function createGame() {
            try {
                const response =
                    await apiFetch(
                        "/api/games",
                        {
                            method: "POST",
                            headers: {
                                "Content-Type":
                                    "application/json",
                            },
                            body: JSON.stringify(
                                {
                                    owner_id:
                                        "LOCAL-USER",
                                    nickname:
                                        "나경",
                                    ai_difficulty:
                                        aiDifficultySelect
                                            .value,
                                }
                            ),
                        }
                    );

                const data =
                    await response.json();

                if (!response.ok) {
                    showMessage(
                        data.message
                        || "게임 생성 실패"
                    );

                    return;
                }

                closeRealtime();

                currentGameId =
                    data.game_id;
                currentGameMode =
                    "SOLO_AI";
                currentOwnerId =
                    "LOCAL-USER";

                const humanPlayer =
                    data.players.find(
                        player =>
                            player.player_type
                            === "HUMAN"
                    );

                currentPlayerId =
                    humanPlayer
                        ? humanPlayer.player_id
                        : null;

                onlinePlayerId.textContent =
                    currentPlayerId
                    || "없음";

                const difficultyLabel =
                    aiDifficultySelect
                        .selectedOptions[0]
                        .textContent
                        .trim();

                showMessage(
                    `게임 생성 완료: `
                    + `${currentGameId}\n`
                    + `AI 난이도: `
                    + `${difficultyLabel}`
                );

                renderGame(data);

            } catch (error) {
                showMessage(
                    `게임 생성 오류: `
                    + `${error}`
                );
            }
        }


        async function refreshGame() {
            if (!currentGameId) {
                showMessage(
                    "먼저 게임을 만들어 주세요."
                );

                return;
            }

            try {
                const refreshUrl =
                    (
                        currentGameMode
                        === "ONLINE"
                    )
                    ? (
                        `/api/online/rooms/`
                        + `${currentGameId}`
                        + `?player_id=`
                        + encodeURIComponent(
                            currentPlayerId
                        )
                        + `&t=${Date.now()}`
                    )
                    : (
                        `/api/games/`
                        + `${currentGameId}`
                        + `?t=${Date.now()}`
                    );

                const response =
                    await apiFetch(
                        refreshUrl,
                        {
                            cache: "no-store",
                        }
                    );

                const data =
                    await response.json();

                if (!response.ok) {
                    showMessage(
                        data.message
                        || "게임 조회 실패"
                    );

                    return;
                }

                renderGame(data);

            } catch (error) {
                showMessage(
                    `게임 조회 오류: `
                    + `${error}`
                );
            }
        }


        function renderGame(game) {
            setUiMode("game");

            const humanPlayer =
                (
                    currentGameMode
                    === "ONLINE"
                    && currentPlayerId
                )
                ? game.players.find(
                    player =>
                        player.player_id
                        === currentPlayerId
                )
                : game.players.find(
                    player =>
                        player.player_type
                        === "HUMAN"
                );

            const currentTurnPlayer =
                game.players.find(
                    player =>
                        player.player_id
                        === game.current_turn_player_id
                );

            gameStatusElement.innerHTML = `
                <div class="status-line status-primary">
                    ${game.round_number}R / 20
                </div>

                <div class="status-line">
                    내 점수
                    <b>${humanPlayer ? humanPlayer.total_score : 0}</b>
                </div>

                <div class="status-line">
                    현재 턴
                    <b>${currentTurnPlayer ? currentTurnPlayer.nickname : "-"}</b>
                </div>

                <div class="status-line status-secondary">
                    덱 ${game.deck_count}
                </div>
            `;

            renderDeclarationStatusBadge(game, humanPlayer);

            renderDealerSelection(
                game
            );

            renderNextRound(
                game
            );

            renderRoundResult(
                game
            );

            renderTieBreak(
                game
            );

            renderPlayers(
                game.players,
                game,
                humanPlayer
            );

            renderMyHand(
                humanPlayer,
                game
            );

            renderDiscardPile(
                game.discard_pile
            );

            const canDraw =
                humanPlayer
                && game.status
                    === "PLAYING"
                && game.turn_phase
                    === "DRAW"
                && game
                    .current_turn_player_id
                    === humanPlayer
                        .player_id;

            drawDeck.disabled =
                !canDraw;
            drawDeck.classList.toggle(
                "is-drawable",
                canDraw
            );

            renderStop(
                game,
                humanPlayer
            );

            renderSurpriseStop(
                game,
                humanPlayer
            );

            renderBombBagaji(
                game,
                humanPlayer
            );

            renderGeneralBagaji(
                game,
                humanPlayer
            );

            renderBbung(
                game,
                humanPlayer
            );
        }


        function renderDealerSelection(
            game
        ) {
            const active =
                game.status
                === "DEALER_SELECTION";

            dealerSelectionPanel.style.display =
                active ? "block" : "none";

            if (!active) {
                dealerSelectionHistory.innerHTML = "";
                dealerDrawButton.style.display = "none";
                confirmOnlineStartButton.style.display = "none";
                return;
            }

            const modeLabel =
                game.dealer_selection_mode === "NIGHT"
                    ? "🌙 밤 — 가장 낮은 월이 선"
                    : "☀️ 낮 — 가장 높은 월이 선";

            dealerSelectionMode.innerHTML = `
                <div class="reaction-title">
                    ${modeLabel}
                </div>
                <div>
                    한국시간 기준 자동 설정 · 각자 직접 1장씩 뽑습니다.
                    동점이면 동점자만 다시 뽑습니다.
                </div>
            `;

            const playerMap = new Map(
                game.players.map(
                    player => [player.player_id, player]
                )
            );

            dealerSelectionHistory.innerHTML = "";

            for (
                const round
                of (game.dealer_selection_history || [])
            ) {
                const block = document.createElement("div");
                block.className = "player";

                const cards = Object.entries(round.draws || {})
                    .map(([playerId, card]) => {
                        const player = playerMap.get(playerId);
                        const name = player ? player.nickname : playerId;
                        const isWinner = (round.winner_ids || [])
                            .includes(playerId);
                        return `
                            <div>
                                <strong>${name}</strong> :
                                ${card.month}월
                                ${isWinner ? "★" : ""}
                            </div>
                        `;
                    })
                    .join("");

                const tied = (round.winner_ids || []).length > 1;
                block.innerHTML = `
                    <div><strong>${round.round}차 추첨</strong></div>
                    ${cards}
                    <div>${tied ? "동점 → 재추첨" : "선 결정"}</div>
                `;
                dealerSelectionHistory.appendChild(block);
            }

            const currentDraws =
                game.dealer_selection_current_draws || {};
            const candidates =
                game.dealer_selection_candidate_ids || [];

            if (!game.dealer_id && candidates.length) {
                const currentBlock = document.createElement("div");
                currentBlock.className = "player dealer-current-round";
                const rows = candidates.map(playerId => {
                    const player = playerMap.get(playerId);
                    const name = player ? player.nickname : playerId;
                    const card = currentDraws[playerId];
                    return `
                        <div>
                            <strong>${name}</strong> :
                            ${card ? `${card.month}월` : "대기 중"}
                        </div>
                    `;
                }).join("");
                currentBlock.innerHTML = `
                    <div><strong>${game.dealer_selection_round_number || 1}차 진행 중</strong></div>
                    ${rows}
                `;
                dealerSelectionHistory.appendChild(currentBlock);
            }

            const dealer = game.players.find(
                player => player.player_id === game.dealer_id
            );

            if (dealer) {
                const result = document.createElement("div");
                result.className = "reaction-title";
                result.textContent = `선: ${dealer.nickname}`;
                dealerSelectionHistory.appendChild(result);
            }

            const isCandidate =
                currentPlayerId
                && candidates.includes(currentPlayerId);
            const alreadyDrew =
                currentPlayerId
                && Boolean(currentDraws[currentPlayerId]);

            dealerDrawButton.style.display =
                (!game.dealer_id && isCandidate)
                    ? "inline-block"
                    : "none";
            dealerDrawButton.disabled =
                !isCandidate || alreadyDrew;
            dealerDrawButton.textContent =
                alreadyDrew
                    ? "다른 플레이어를 기다리는 중"
                    : "선 정하기 카드 뽑기";

            confirmOnlineStartButton.style.display =
                (
                    currentGameMode === "ONLINE"
                    && currentOwnerId
                    && game.dealer_id
                )
                    ? "inline-block"
                    : "none";
        }


        function renderNextRound(
            game
        ) {
            nextRoundPanel.style.display =
                (
                    game.status === "ROUND_END"
                    ? "block"
                    : "none"
                );
        }


        function getRoundEndReasonLabel(
            game
        ) {
            const reason =
                game.round_end_reason;

            if (reason === "NORMAL_STOP") {
                const stopType =
                    game.declared_stop_type;

                const stopLabels = {
                    STRAIGHT:
                        "스트레이트 STOP",
                    HIGH_SUM:
                        "60 이상 STOP",
                    TTOI_TTOI:
                        "또이또이 STOP",
                    MINUS_100:
                        "-100 STOP",
                    MINUS_200:
                        "-200 STOP",
                };

                return (
                    stopLabels[stopType]
                    || "일반 STOP"
                );
            }

            const labels = {
                BAGAJI:
                    "일반 바가지",
                BOMB_BAGAJI:
                    "폭탄 바가지",
                SURPRISE_STOP:
                    (
                        game.surprise_stop_dokbak
                        ? "기습 STOP + 독박"
                        : "기습 STOP"
                    ),
                DECK_EXHAUSTED:
                    (
                        game
                            .round_winner_decided_by_tie_break
                        ? (
                            `${game.play_phase}페이즈 `
                            + "덱 소진 + 3장 승부"
                        )
                        : (
                            `${game.play_phase}페이즈 `
                            + "덱 소진"
                        )
                    ),
            };

            return (
                labels[reason]
                || reason
                || "알 수 없음"
            );
        }


        function renderTieBreak(
            game
        ) {
            const active =
                game.status
                === "TIE_BREAK";

            tieBreakPanel.style.display =
                active
                    ? "block"
                    : "none";

            tieBreakInfo.innerHTML = "";
            tieBreakDrawButton.disabled =
                true;

            if (!active) {
                return;
            }

            const participantIds =
                game.tie_break_player_ids
                || [];

            const drawnMap =
                game.tie_break_drawn_cards
                || {};

            const currentId =
                game.tie_break_current_player_id;

            const playerMap =
                new Map(
                    game.players.map(
                        player => [
                            player.player_id,
                            player,
                        ]
                    )
                );

            const roundLabel =
                game.tie_break_round_number
                || 1;

            const header =
                document.createElement(
                    "div"
                );

            header.className =
                "reaction-title";

            header.textContent =
                `${roundLabel}차 3장 승부`;

            tieBreakInfo.appendChild(
                header
            );

            for (
                const playerId
                of participantIds
            ) {
                const player =
                    playerMap.get(
                        playerId
                    );

                const cards =
                    drawnMap[playerId]
                    || [];

                const score =
                    cards.reduce(
                        (
                            total,
                            card
                        ) =>
                            total
                            + card.month,
                        0
                    );

                const row =
                    document.createElement(
                        "div"
                    );

                row.className =
                    "player";

                row.innerHTML = `
                    <strong>
                        ${
                            player
                                ? player.nickname
                                : playerId
                        }
                    </strong>
                    ${
                        playerId === currentId
                            ? " ← 현재 차례"
                            : ""
                    }
                    <div>
                        공개 카드:
                        ${
                            cards.length
                                ? cards
                                    .map(
                                        card =>
                                            `${card.month}월`
                                    )
                                    .join(", ")
                                : "아직 없음"
                        }
                    </div>
                    <div>
                        현재 합:
                        ${score}
                    </div>
                `;

                tieBreakInfo.appendChild(
                    row
                );
            }

            const myTurn =
                (
                    currentPlayerId
                    && participantIds.includes(
                        currentPlayerId
                    )
                    && currentId
                        === currentPlayerId
                );

            tieBreakDrawButton.disabled =
                !myTurn;
        }


        function renderDeclarationStatusBadge(game, humanPlayer) {
            if (!declarationStatusBadge) {
                return;
            }

            declarationStatusBadge.style.display = "none";
            declarationStatusBadge.textContent = "";

            if (!game || !humanPlayer) {
                return;
            }

            const bomb = (game.active_bomb_bagaji_declarations || []).find(
                item => item.player_id === humanPlayer.player_id
            );
            const general = (game.active_bagaji_declarations || []).find(
                item => item.player_id === humanPlayer.player_id
            );

            if (bomb) {
                declarationStatusBadge.textContent = `폭탄 바가지 선언 중 · ${bomb.month}월`;
                declarationStatusBadge.style.display = "inline-flex";
                return;
            }

            if (general) {
                declarationStatusBadge.textContent = `바가지 선언 중 · ${general.month}월`;
                declarationStatusBadge.style.display = "inline-flex";
            }
        }

        function renderRoundResult(
            game
        ) {
            roundResultPanel.style.display =
                "none";

            roundResultElement.innerHTML =
                "";

            if (
                game.status !== "ROUND_END"
                && game.status !== "GAME_END"
            ) {
                return;
            }

            roundResultPanel.style.display =
                "block";

            const myPlayerId = currentPlayerId || (
                game.players.find(player => player.player_type === "HUMAN")?.player_id
            );
            const winnerId = game.status === "GAME_END"
                ? game.game_winner_id
                : game.round_winner_id;
            const resultSoundKey = `${game.status}:${game.round_number}:${winnerId || "none"}:${myPlayerId || "none"}`;

            if (lastResultSoundKey !== resultSoundKey) {
                lastResultSoundKey = resultSoundKey;
                if (myPlayerId && winnerId === myPlayerId) {
                    playEffect("win");
                } else if (myPlayerId && winnerId) {
                    playElderlyAigo();
                }
            }

            if (game.status === "GAME_END") {
                const gameWinner =
                    game.players.find(
                        player =>
                            player.player_id
                            === game.game_winner_id
                    );

                roundResultElement.innerHTML = `
                    <div>
                        <strong>
                            최종 승자:
                        </strong>
                        ${
                            gameWinner
                                ? gameWinner.nickname
                                : (
                                    game.game_winner_id
                                    || "없음"
                                )
                        }
                    </div>
                `;

                return;
            }

            const winner =
                game.players.find(
                    player =>
                        player.player_id
                        === game.round_winner_id
                );

            const winnerName =
                winner
                    ? winner.nickname
                    : (
                        game.round_winner_id
                        || "없음"
                    );

            const reasonLabel =
                getRoundEndReasonLabel(
                    game
                );

            roundResultElement.innerHTML = `
                <div>
                    <strong>
                        이번 판 승리:
                    </strong>
                    ${winnerName}
                </div>

                <div>
                    <strong>
                        승리 방식:
                    </strong>
                    ${reasonLabel}
                </div>
            `;
        }


        function renderPlayers(
            players,
            game,
            humanPlayer
        ) {
            playersElement.innerHTML = "";

            const revealHands =
                game.status === "ROUND_END"
                || game.status === "GAME_END";

            const opponents = players.filter(
                player =>
                    !humanPlayer
                    || player.player_id
                        !== humanPlayer.player_id
            );

            playersElement.dataset.opponents =
                String(opponents.length);

            for (
                let index = 0;
                index < opponents.length;
                index += 1
            ) {
                const player = opponents[index];
                const element =
                    document.createElement("div");

                element.className =
                    `player seat seat-${index + 1}`;

                if (
                    game.current_turn_player_id
                    === player.player_id
                ) {
                    element.classList.add(
                        "is-current-turn"
                    );
                }

                let handHtml = "";

                if (
                    revealHands
                    && player.hand
                    && player.hand.length
                ) {
                    const cardsHtml =
                        player.hand
                            .map(
                                card => `
                                    <span class="card">
                                        ${cardMarkup(card)}
                                    </span>
                                `
                            )
                            .join("");

                    handHtml = `
                        <div class="opponent-hand">
                            ${cardsHtml}
                        </div>
                    `;
                }

                element.innerHTML = `
                    <div class="player-head">
                        <strong>${player.nickname}</strong>
                        <span>${player.hand_count}장</span>
                    </div>
                    <div class="player-score-row">
                        <span>합계 ${player.total_score}</span>
                        <span>이번 판 ${player.round_score}</span>
                    </div>
                    ${
                        player.bbung_count
                            ? `<div class="bbung-count">뻥 ${player.bbung_count}</div>`
                            : ""
                    }
                    ${handHtml}
                `;

                playersElement.appendChild(
                    element
                );
            }
        }



        function renderMyHand(
            player,
            game
        ) {
            myHandElement.innerHTML =
                "";

            if (!player) {
                myHandElement
                    .textContent =
                    "인간 플레이어가 없습니다.";

                return;
            }

            for (
                const card
                of player.hand
            ) {
                const button =
                    document
                        .createElement(
                            "button"
                        );

                button.className =
                    "card";

                button.innerHTML =
                    cardMarkup(card);

                const isMyTurn =
                    game
                        .current_turn_player_id
                    === player.player_id;

                const canDiscard =
                    game.status
                        === "PLAYING"
                    && game.turn_phase
                        === "DISCARD"
                    && isMyTurn;

                button.disabled =
                    !canDiscard;

                button
                    .addEventListener(
                        "click",
                        () => {
                            discardCard(
                                card.card_id
                            );
                        }
                    );

                myHandElement
                    .appendChild(
                        button
                    );
            }
        }


        function renderDiscardPile(
            cards
        ) {
            discardPileElement
                .innerHTML = "";

            if (
                !cards
                || cards.length === 0
            ) {
                discardPileElement
                    .textContent =
                    "없음";

                return;
            }

            const visibleCards =
                cards.slice(-5);

            for (
                const card
                of visibleCards
            ) {
                const element =
                    document
                        .createElement(
                            "span"
                        );

                element.className =
                    "card";

                element.innerHTML =
                    cardMarkup(card);

                discardPileElement
                    .appendChild(
                        element
                    );
            }
        }


        function getStopLabel(
            stopType
        ) {
            const labels = {
                "STRAIGHT": "스트레이트",
                "HIGH_SUM": "60 이상",
                "TTOI_TTOI": "또이또이",
                "MINUS_100": "-100",
                "MINUS_200": "-200",
            };

            return (
                labels[stopType]
                || stopType
            );
        }


        function renderStop(
            game,
            humanPlayer
        ) {
            stopPanel.style.display =
                "none";

            stopButtons.style.display =
                "none";

            stopButtons.innerHTML =
                "";

            if (!humanPlayer) {
                return;
            }

            const canCallStop =
                game.status
                    === "PLAYING"
                && game.turn_phase
                    === "DISCARD"
                && game
                    .current_turn_player_id
                    === humanPlayer
                        .player_id
                && humanPlayer.hand_count
                    === 6;

            if (!canCallStop) {
                return;
            }

            stopPanel.style.display =
                "block";
        }


        function openStopChoices() {
            stopButtons.innerHTML =
                "";

            const stopTypes = [
                "STRAIGHT",
                "HIGH_SUM",
                "TTOI_TTOI",
                "MINUS_100",
                "MINUS_200",
            ];

            for (
                const stopType
                of stopTypes
            ) {
                const button =
                    document
                        .createElement(
                            "button"
                        );

                button.textContent =
                    getStopLabel(
                        stopType
                    );

                button.addEventListener(
                    "click",
                    () => {
                        declareStop(
                            stopType
                        );
                    }
                );

                stopButtons
                    .appendChild(
                        button
                    );
            }

            const cancelButton =
                document
                    .createElement(
                        "button"
                    );

            cancelButton.textContent =
                "취소";

            cancelButton.addEventListener(
                "click",
                () => {
                    stopButtons.style.display =
                        "none";
                }
            );

            stopButtons.appendChild(
                cancelButton
            );

            stopButtons.style.display =
                "block";
        }


        function getMonthCounts(cards) {
            const counts = new Map();

            for (const card of (cards || [])) {
                counts.set(
                    card.month,
                    (counts.get(card.month) || 0) + 1
                );
            }

            return counts;
        }


        function hasAnyMyBagajiDeclaration(
            game,
            humanPlayer
        ) {
            if (!humanPlayer) {
                return false;
            }

            const general = (
                game.active_bagaji_declarations
                || []
            ).some(
                item => item.player_id
                    === humanPlayer.player_id
            );

            const bomb = (
                game.active_bomb_bagaji_declarations
                || []
            ).some(
                item => item.player_id
                    === humanPlayer.player_id
            );

            return general || bomb;
        }


        function canShowSurpriseStop(
            game,
            humanPlayer
        ) {
            if (
                !humanPlayer
                || game.status !== "PLAYING"
                || game.turn_phase !== "DRAW"
                || game.current_turn_player_id
                    !== humanPlayer.player_id
                || humanPlayer.hand.length !== 2
                || humanPlayer.bbung_count <= 0
            ) {
                return false;
            }

            const handSum = humanPlayer.hand.reduce(
                (sum, card) => sum + card.month,
                0
            );

            if (handSum > 5) {
                return false;
            }

            const bbungPlayerCount = (
                game.players || []
            ).filter(
                player => player.bbung_count > 0
            ).length;

            const requiredCount =
                (game.players || []).length === 3
                    ? 2
                    : 3;

            return bbungPlayerCount >= requiredCount;
        }


        function getGeneralBagajiTargetMonth(
            humanPlayer
        ) {
            if (
                !humanPlayer
                || humanPlayer.bbung_count <= 0
                || humanPlayer.hand.length !== 2
            ) {
                return null;
            }

            const [first, second] = humanPlayer.hand;

            if (
                !first
                || !second
                || first.month !== second.month
            ) {
                return null;
            }

            return first.month;
        }


        function getBombBagajiTargetMonth(
            humanPlayer
        ) {
            if (
                !humanPlayer
                || humanPlayer.hand.length !== 5
            ) {
                return null;
            }

            const counts = getMonthCounts(
                humanPlayer.hand
            );

            const values = Array.from(
                counts.values()
            ).sort((a, b) => a - b);

            if (
                values.length !== 2
                || values[0] !== 2
                || values[1] !== 3
            ) {
                return null;
            }

            for (const [month, count] of counts) {
                if (count === 2) {
                    return month;
                }
            }

            return null;
        }


        function renderSurpriseStop(
            game,
            humanPlayer
        ) {
            surpriseStopPanel.style.display =
                canShowSurpriseStop(
                    game,
                    humanPlayer
                )
                    ? "block"
                    : "none";
        }


        function renderBombBagaji(
            game,
            humanPlayer
        ) {
            bombBagajiPanel.style.display =
                "none";

            bombBagajiCallButton.style.display =
                "none";

            bombBagajiStatus.textContent =
                "";

            if (
                !humanPlayer
                || game.status !== "PLAYING"
            ) {
                return;
            }

            const activeDeclarations =
                game.active_bomb_bagaji_declarations
                || [];

            const myDeclaration =
                activeDeclarations.find(
                    declaration =>
                        declaration.player_id
                        === humanPlayer.player_id
                );

            if (myDeclaration) {
                return;
            }

            if (
                hasAnyMyBagajiDeclaration(
                    game,
                    humanPlayer
                )
            ) {
                return;
            }

            const targetMonth =
                getBombBagajiTargetMonth(
                    humanPlayer
                );

            if (targetMonth === null) {
                return;
            }

            bombBagajiPanel.style.display =
                "block";

            bombBagajiStatus.textContent =
                `${targetMonth}월 폭탄 바가지 가능`;

            bombBagajiCallButton.style.display =
                "inline-block";
        }


        function renderGeneralBagaji(
            game,
            humanPlayer
        ) {
            generalBagajiPanel.style.display =
                "none";

            generalBagajiCallButton.style.display =
                "none";

            generalBagajiStatus.textContent =
                "";

            if (
                !humanPlayer
                || game.status !== "PLAYING"
            ) {
                return;
            }

            const activeDeclarations =
                game.active_bagaji_declarations
                || [];

            const myDeclaration =
                activeDeclarations.find(
                    declaration =>
                        declaration.player_id
                        === humanPlayer.player_id
                );

            if (myDeclaration) {
                return;
            }

            if (
                hasAnyMyBagajiDeclaration(
                    game,
                    humanPlayer
                )
            ) {
                return;
            }

            const targetMonth =
                getGeneralBagajiTargetMonth(
                    humanPlayer
                );

            if (targetMonth === null) {
                return;
            }

            generalBagajiPanel.style.display =
                "block";

            generalBagajiStatus.textContent =
                `${targetMonth}월 일반 바가지 가능`;

            generalBagajiCallButton.style.display =
                "inline-block";
        }


        function renderBbung(
            game,
            humanPlayer
        ) {
            bbungPanel.style.display =
                "none";

            bbungExtraCards.innerHTML =
                "";

            bbungConfirmButton.disabled =
                true;

            selectedBbungExtraCardId =
                null;

            currentBbungMatchingCardIds =
                [];

            if (!humanPlayer) {
                return;
            }

            const candidates =
                game
                    .bbung_candidate_player_ids
                || [];

            const isCandidate =
                game.status
                    === "PLAYING"
                && game.turn_phase
                    === "REACTION"
                && candidates.includes(
                    humanPlayer.player_id
                );

            if (!isCandidate) {
                return;
            }

            const discardedCard =
                game.last_discarded_card;

            if (!discardedCard) {
                return;
            }

            const matchingCards =
                humanPlayer.hand.filter(
                    card =>
                        card.month
                        === discardedCard.month
                );

            if (
                matchingCards.length < 2
            ) {
                return;
            }

            /*
             * 현재 테스트 UI에서는
             * 같은 월 카드가 3장 이상이면
             * 앞의 2장을 뻥 카드로 사용한다.
             *
             * 나중에 실제 화투 이미지 UI에서
             * 직접 2장 선택 방식으로 바꿀 예정.
             */
            currentBbungMatchingCardIds =
                matchingCards
                    .slice(0, 2)
                    .map(
                        card =>
                            card.card_id
                    );

            const extraCards =
                humanPlayer.hand.filter(
                    card =>
                        !currentBbungMatchingCardIds
                            .includes(
                                card.card_id
                            )
                );

            bbungMessage.textContent =
                `${discardedCard.month}월 `
                + "뻥 가능! "
                + "추가로 버릴 카드 "
                + "1장을 선택하세요.";

            for (
                const card
                of extraCards
            ) {
                const button =
                    document
                        .createElement(
                            "button"
                        );

                button.className =
                    "card";

                button.innerHTML =
                    cardMarkup(card);

                button
                    .addEventListener(
                        "click",
                        () => {
                            selectedBbungExtraCardId =
                                card.card_id;

                            const buttons =
                                bbungExtraCards
                                    .querySelectorAll(
                                        ".card"
                                    );

                            for (
                                const targetButton
                                of buttons
                            ) {
                                targetButton
                                    .classList
                                    .remove(
                                        "selected-card"
                                    );
                            }

                            button
                                .classList
                                .add(
                                    "selected-card"
                                );

                            bbungConfirmButton
                                .disabled =
                                false;
                        }
                    );

                bbungExtraCards
                    .appendChild(
                        button
                    );
            }

            bbungPanel.style.display =
                "block";
        }


        async function drawCard() {
            if (!currentGameId) {
                showMessage(
                    "먼저 게임을 만들어 주세요."
                );

                return;
            }

            try {
                const response =
                    await apiFetch(
                        `/api/games/`
                        + `${currentGameId}`
                        + `/draw`,
                        {
                            method: "POST",
                        }
                    );

                const data =
                    await response.json();

                if (!response.ok) {
                    showMessage(
                        data.message
                        || "카드 뽑기 실패"
                    );

                    return;
                }

                if (data.drawn_card) {
                    playEffect("draw");
                    showMessage(
                        `${data.drawn_card.month}월 `
                        + "카드를 뽑았습니다."
                    );
                } else {
                    showMessage(
                        "덱이 소진되어 "
                        + "라운드가 종료되었습니다."
                    );
                }

                await refreshAfterAction();

            } catch (error) {
                showMessage(
                    `카드 뽑기 오류: `
                    + `${error}`
                );
            }
        }


        async function discardCard(
            cardId
        ) {
            if (!currentGameId) {
                return;
            }

            try {
                const response =
                    await apiFetch(
                        `/api/games/`
                        + `${currentGameId}`
                        + `/discard`,
                        {
                            method: "POST",
                            headers: {
                                "Content-Type":
                                    "application/json",
                            },
                            body:
                                JSON.stringify(
                                    {
                                        card_id:
                                            cardId,
                                    }
                                ),
                        }
                    );

                const data =
                    await response.json();

                if (!response.ok) {
                    showMessage(
                        data.message
                        || "카드 버리기 실패"
                    );

                    return;
                }

                playEffect("discard");

                showMessage(
                    `${data.discarded_card.month}월 `
                    + "카드를 버렸습니다."
                );

                await refreshAfterAction();

                if (
                    currentGameMode
                    === "SOLO_AI"
                    && data.status
                    === "PLAYING"
                ) {
                    await continueGame();
                }

            } catch (error) {
                showMessage(
                    `카드 버리기 오류: `
                    + `${error}`
                );
            }
        }


        async function drawTieBreakCard() {
            if (
                !currentGameId
                || !currentPlayerId
            ) {
                return;
            }

            tieBreakDrawButton.disabled =
                true;

            try {
                const response =
                    await apiFetch(
                        `/api/games/`
                        + `${currentGameId}`
                        + `/tie-break/draw`,
                        {
                            method: "POST",
                        }
                    );

                const data =
                    await response.json();

                if (!response.ok) {
                    showMessage(
                        data.message
                        || "3장 승부 드로우 실패"
                    );
                    return;
                }

                const card =
                    data
                        .drawn_tie_break_card;

                if (data.status === "GAME_END") {
                    const winner =
                        data.players.find(
                            player =>
                                player.player_id
                                === data.game_winner_id
                        );

                    showMessage(
                        `승부 카드: `
                        + `${card.month}월\n`
                        + `최종 승자: `
                        + `${
                            winner
                                ? winner.nickname
                                : data.game_winner_id
                        }`
                    );
                } else {
                    showMessage(
                        `승부 카드: `
                        + `${card.month}월`
                    );
                }

                await refreshAfterAction();

            } catch (error) {
                showMessage(
                    `3장 승부 오류: ${error}`
                );
            }
        }


        async function startNextRound() {
            if (!currentGameId) {
                return;
            }

            try {
                const response =
                    await apiFetch(
                        `/api/games/`
                        + `${currentGameId}`
                        + `/next-round`,
                        {
                            method: "POST",
                        }
                    );

                const data =
                    await response.json();

                if (!response.ok) {
                    showMessage(
                        data.message
                        || "다음 라운드 시작 실패"
                    );

                    return;
                }

                if (data.status === "PLAYING") {
                    showMessage(
                        `${data.round_number}라운드 시작`
                    );
                } else {
                    showMessage(
                        `상태: ${data.status}`
                    );
                }

                await refreshAfterAction();

            } catch (error) {
                showMessage(
                    `다음 라운드 오류: ${error}`
                );
            }
        }


        async function continueGame() {
            if (!currentGameId) {
                showMessage(
                    "먼저 게임을 만들어 주세요."
                );

                return;
            }

            try {
                const response =
                    await apiFetch(
                        `/api/games/`
                        + `${currentGameId}`
                        + `/continue`,
                        {
                            method: "POST",
                        }
                    );

                const data =
                    await response.json();

                if (!response.ok) {
                    showMessage(
                        data.message
                        || "AI 진행 실패"
                    );

                    return;
                }

                if (
                    data.turn_phase
                    === "REACTION"
                    && (
                        data
                            .bbung_candidate_player_ids
                        || []
                    ).length > 0
                ) {
                    showMessage(
                        "뻥 가능한 카드가 있습니다. "
                        + "뻥 또는 넘기기를 "
                        + "선택하세요."
                    );
                } else {
                    showMessage(
                        `AI 진행 완료\n`
                        + `AI 처리 턴: `
                        + `${data.ai_turn_count ?? 0}`
                    );
                }

                // /continue는 원칙적으로 전체 게임 상태를 반환한다.
                // 혹시 불완전한 응답이 오더라도 화면이 죽지 않도록
                // players 배열을 확인한 뒤 필요하면 다시 조회한다.
                if (
                    Array.isArray(
                        data.players
                    )
                ) {
                    renderGame(
                        data
                    );
                } else {
                    await refreshGame();
                }

            } catch (error) {
                showMessage(
                    `AI 진행 오류: `
                    + `${error}`
                );
            }
        }


        async function declareStop(
            stopType
        ) {
            if (!currentGameId) {
                return;
            }

            const stopLabel =
                getStopLabel(
                    stopType
                );

            try {
                const response =
                    await apiFetch(
                        `/api/games/`
                        + `${currentGameId}`
                        + `/stop`,
                        {
                            method: "POST",
                            headers: {
                                "Content-Type":
                                    "application/json",
                            },
                            body:
                                JSON.stringify(
                                    {
                                        stop_type:
                                            stopType,
                                    }
                                ),
                        }
                    );

                const data =
                    await response.json();

                if (!response.ok) {
                    showMessage(
                        data.message
                        || "STOP 선언 실패"
                    );

                    return;
                }

                showMessage(
                    `${stopLabel} STOP 선언!\n`
                    + `점수: ${data.score}\n`
                    + "라운드가 종료되었습니다."
                );

                await refreshAfterAction();

            } catch (error) {
                showMessage(
                    `STOP 오류: `
                    + `${error}`
                );
            }
        }


        async function declareBombBagaji() {
            if (!currentGameId) {
                return;
            }

            try {
                const response =
                    await apiFetch(
                        `/api/games/`
                        + `${currentGameId}`
                        + `/bagaji/bomb`,
                        {
                            method: "POST",
                        }
                    );

                const data =
                    await response.json();

                if (!response.ok) {
                    showMessage(
                        data.message
                        || "폭탄 바가지 선언 실패"
                    );

                    return;
                }

                playEffect("bomb");
                showMessage(
                    "폭탄 바가지 선언!"
                );

                await refreshAfterAction();

            } catch (error) {
                showMessage(
                    `폭탄 바가지 오류: `
                    + `${error}`
                );
            }
        }


        async function cancelBombBagaji() {
            if (!currentGameId) {
                return;
            }

            try {
                const response =
                    await apiFetch(
                        `/api/games/`
                        + `${currentGameId}`
                        + `/bagaji/bomb/cancel`,
                        {
                            method: "POST",
                        }
                    );

                const data =
                    await response.json();

                if (!response.ok) {
                    showMessage(
                        data.message
                        || "폭탄 바가지 철회 실패"
                    );

                    return;
                }

                showMessage(
                    "폭탄 바가지를 철회했습니다."
                );

                await refreshAfterAction();

            } catch (error) {
                showMessage(
                    `폭탄 바가지 철회 오류: `
                    + `${error}`
                );
            }
        }


        async function declareGeneralBagaji() {
            if (!currentGameId) {
                return;
            }

            try {
                const response =
                    await apiFetch(
                        `/api/games/`
                        + `${currentGameId}`
                        + `/bagaji/general`,
                        {
                            method: "POST",
                        }
                    );

                const data =
                    await response.json();

                if (!response.ok) {
                    showMessage(
                        data.message
                        || "일반 바가지 선언 실패"
                    );

                    return;
                }

                playEffect("bagaji");
                showMessage(
                    "일반 바가지 선언!"
                );

                await refreshAfterAction();

            } catch (error) {
                showMessage(
                    `일반 바가지 오류: `
                    + `${error}`
                );
            }
        }


        async function cancelGeneralBagaji() {
            if (!currentGameId) {
                return;
            }

            try {
                const response =
                    await apiFetch(
                        `/api/games/`
                        + `${currentGameId}`
                        + `/bagaji/general/cancel`,
                        {
                            method: "POST",
                        }
                    );

                const data =
                    await response.json();

                if (!response.ok) {
                    showMessage(
                        data.message
                        || "바가지 철회 실패"
                    );

                    return;
                }

                showMessage(
                    "일반 바가지를 철회했습니다."
                );

                await refreshAfterAction();

            } catch (error) {
                showMessage(
                    `바가지 철회 오류: `
                    + `${error}`
                );
            }
        }


        async function declareSurpriseStop() {
            if (!currentGameId) {
                return;
            }

            try {
                const response =
                    await apiFetch(
                        `/api/games/`
                        + `${currentGameId}`
                        + `/surprise-stop`,
                        {
                            method: "POST",
                        }
                    );

                const data =
                    await response.json();

                if (!response.ok) {
                    showMessage(
                        data.message
                        || "기습 STOP 선언 실패"
                    );

                    return;
                }

                let message =
                    `기습 STOP 선언!\n`
                    + `점수: ${data.score}\n`;

                if (
                    data.surprise_stop_dokbak
                ) {
                    message +=
                        "독박 적용: +50\n";
                }

                message +=
                    "라운드가 종료되었습니다.";

                showMessage(
                    message
                );

                await refreshAfterAction();

            } catch (error) {
                showMessage(
                    `기습 STOP 오류: `
                    + `${error}`
                );
            }
        }


        async function declareBbung() {
            if (
                !currentGameId
                || !selectedBbungExtraCardId
                || currentBbungMatchingCardIds
                    .length !== 2
            ) {
                return;
            }

            try {
                const response =
                    await apiFetch(
                        `/api/games/`
                        + `${currentGameId}`
                        + `/bbung`,
                        {
                            method: "POST",
                            headers: {
                                "Content-Type":
                                    "application/json",
                            },
                            body:
                                JSON.stringify(
                                    {
                                        matching_card_ids:
                                            currentBbungMatchingCardIds,

                                        extra_discard_card_id:
                                            selectedBbungExtraCardId,
                                    }
                                ),
                        }
                    );

                const data =
                    await response.json();

                if (!response.ok) {
                    showMessage(
                        data.message
                        || "뻥 실패"
                    );

                    return;
                }

                playEffect("bbung");

                if (
                    data.turn_phase
                    === "REACTION"
                    && (
                        data
                            .bbung_candidate_player_ids
                        || []
                    ).length > 0
                ) {
                    showMessage(
                        "뻥 성공. "
                        + "새 버림패에 다시 "
                        + "반응이 필요합니다."
                    );
                } else {
                    showMessage(
                        "뻥을 선언했습니다."
                    );
                }

                await refreshAfterAction();

            } catch (error) {
                showMessage(
                    `뻥 오류: `
                    + `${error}`
                );
            }
        }


        async function passBbung() {
            if (!currentGameId) {
                return;
            }

            try {
                const response =
                    await apiFetch(
                        `/api/games/`
                        + `${currentGameId}`
                        + `/bbung/pass`,
                        {
                            method: "POST",
                        }
                    );

                const data =
                    await response.json();

                if (!response.ok) {
                    showMessage(
                        data.message
                        || "뻥 넘기기 실패"
                    );

                    return;
                }

                showMessage(
                    "뻥하지 않고 넘겼습니다."
                );

                await refreshAfterAction();

            } catch (error) {
                showMessage(
                    `뻥 넘기기 오류: `
                    + `${error}`
                );
            }
        }


        homeButton.addEventListener(
            "click",
            () => {
                if (currentAuthUser) {
                    setUiMode("lobby");
                    refreshPublicRooms();
                } else {
                    setUiMode("auth");
                }
            }
        );

        backToLobbyButton.addEventListener(
            "click",
            () => {
                setUiMode(currentAuthUser ? "lobby" : "auth");
                if (currentAuthUser) {
                    refreshPublicRooms();
                }
            }
        );

        musicToggle.addEventListener(
            "click",
            () => {
                musicEnabled = !musicEnabled;
                musicToggle.classList.toggle("is-off", !musicEnabled);

                if (!musicEnabled) {
                    lobbyBgm.pause();
                    gameBgm.pause();
                    return;
                }

                setUiMode(
                    gameView.hidden
                        ? (currentAuthUser ? "lobby" : "auth")
                        : "game"
                );
            }
        );

        soundToggle.addEventListener(
            "click",
            () => {
                soundEnabled = !soundEnabled;
                soundToggle.classList.toggle("is-off", !soundEnabled);
            }
        );

        setUiMode("lobby");

        registerButton
            .addEventListener(
                "click",
                registerAccount
            );

        loginButton
            .addEventListener(
                "click",
                loginAccount
            );

        logoutButton
            .addEventListener(
                "click",
                logoutAccount
            );

        refreshAuth();

        window.setInterval(
            () => {
                if (
                    currentAuthUser
                    && !lobbyView.hidden
                ) {
                    refreshPublicRooms();
                }
            },
            5000
        );

        const invitedRoomId =
            normalizeRoomId(
                new URLSearchParams(
                    window.location.search
                ).get(
                    "room"
                )
            );

        if (invitedRoomId) {
            onlineRoomId.value =
                invitedRoomId;
            joinRoomId.value =
                invitedRoomId;

            if (authToken) {
                openModal(
                    roomJoinModal
                );
            } else {
                showMessage(
                    "초대받은 방이 있습니다. 로그인 후 참가를 눌러 주세요."
                );
            }
        }

        confirmOnlineStartButton
            .addEventListener(
                "click",
                confirmOnlineGameStart
            );

        document
            .getElementById(
                "createOnlineRoomButton"
            )
            .addEventListener(
                "click",
                openCreateRoomModal
            );

        document
            .getElementById(
                "joinOnlineRoomButton"
            )
            .addEventListener(
                "click",
                openJoinRoomModal
            );

        document
            .getElementById(
                "confirmCreateOnlineRoomButton"
            )
            .addEventListener(
                "click",
                createOnlineRoom
            );

        document
            .getElementById(
                "confirmJoinOnlineRoomButton"
            )
            .addEventListener(
                "click",
                joinOnlineRoom
            );

        document
            .getElementById(
                "copyInviteLinkButton"
            )
            .addEventListener(
                "click",
                copyInviteLink
            );

        document
            .getElementById(
                "rulesButton"
            )
            .addEventListener(
                "click",
                () => openModal(
                    rulesModal
                )
            );


        document
            .getElementById(
                "rulesLobbyButton"
            )
            .addEventListener(
                "click",
                () => openModal(
                    rulesModal
                )
            );

        refreshPublicRoomsButton
            .addEventListener(
                "click",
                refreshPublicRooms
            );

        document
            .querySelectorAll(
                '[data-close-modal]'
            )
            .forEach(
                button => {
                    button.addEventListener(
                        "click",
                        () => closeModal(
                            document.getElementById(
                                button.dataset.closeModal
                            )
                        )
                    );
                }
            );

        document
            .querySelectorAll(
                '.modal-backdrop'
            )
            .forEach(
                modal => {
                    modal.addEventListener(
                        "click",
                        event => {
                            if (
                                event.target
                                === modal
                            ) {
                                closeModal(
                                    modal
                                );
                            }
                        }
                    );
                }
            );

        document
            .querySelectorAll(
                'input[name="roomPrivacy"]'
            )
            .forEach(
                radio => {
                    radio.addEventListener(
                        "change",
                        () => {
                            const isPrivate =
                                getSelectedRoomPrivacy()
                                === "PRIVATE";

                            roomPasswordCreateWrap.hidden =
                                !isPrivate;

                            if (!isPrivate) {
                                roomPasswordCreate.value = "";
                            }
                        }
                    );
                }
            );

        document
            .getElementById(
                "startOnlineRoomButton"
            )
            .addEventListener(
                "click",
                startOnlineRoom
            );

        document
            .getElementById(
                "createGameButton"
            )
            .addEventListener(
                "click",
                createGame
            );

        document
            .getElementById(
                "refreshButton"
            )
            .addEventListener(
                "click",
                refreshGame
            );

        drawDeck
            .addEventListener(
                "click",
                drawCard
            );

        dealerDrawButton
            .addEventListener(
                "click",
                drawDealerSelectionCard
            );

        stopCallButton
            .addEventListener(
                "click",
                openStopChoices
            );

        tieBreakDrawButton
            .addEventListener(
                "click",
                drawTieBreakCard
            );

        nextRoundButton
            .addEventListener(
                "click",
                startNextRound
            );

        bombBagajiCallButton
            .addEventListener(
                "click",
                declareBombBagaji
            );


        generalBagajiCallButton
            .addEventListener(
                "click",
                declareGeneralBagaji
            );


        surpriseStopButton
            .addEventListener(
                "click",
                declareSurpriseStop
            );

        bbungConfirmButton
            .addEventListener(
                "click",
                declareBbung
            );

        bbungPassButton
            .addEventListener(
                "click",
                passBbung
            );
