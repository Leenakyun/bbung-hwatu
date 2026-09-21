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

        const registerUsername =
            document.getElementById(
                "registerUsername"
            );

        const registerPassword =
            document.getElementById(
                "registerPassword"
            );

        const loginForm =
            document.getElementById(
                "loginForm"
            );

        const registerForm =
            document.getElementById(
                "registerForm"
            );

        const registerPanel =
            document.getElementById(
                "registerPanel"
            );

        const showRegisterButton =
            document.getElementById(
                "showRegisterButton"
            );

        const showLoginButton =
            document.getElementById(
                "showLoginButton"
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

        const beginnerTutorialOption =
            document.getElementById(
                "beginnerTutorialOption"
            );

        const beginnerTutorialToggle =
            document.getElementById(
                "beginnerTutorialToggle"
            );

        const beginnerTutorialLevel =
            document.getElementById(
                "beginnerTutorialLevel"
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
        const settingsButton = document.getElementById("settingsButton");
        const settingsModal = document.getElementById("settingsModal");
        const bgmVolumeInput = document.getElementById("bgmVolume");
        const sfxVolumeInput = document.getElementById("sfxVolume");
        const voiceVolumeInput = document.getElementById("voiceVolume");
        const bgmVolumeValue = document.getElementById("bgmVolumeValue");
        const sfxVolumeValue = document.getElementById("sfxVolumeValue");
        const voiceVolumeValue = document.getElementById("voiceVolumeValue");
        const vibrationToggle = document.getElementById("vibrationToggle");
        const saveSettingsButton = document.getElementById("saveSettingsButton");
        const declarationStatusBadge = document.getElementById("declarationStatusBadge");
        const lobbyBgm = document.getElementById("lobbyBgm");
        const gameBgm = document.getElementById("gameBgm");
        const tutorialGuide = document.getElementById("tutorialGuide");
        const tutorialGuideTitle = document.getElementById("tutorialGuideTitle");
        const tutorialGuideText = document.getElementById("tutorialGuideText");
        const tutorialGuideOffButton = document.getElementById("tutorialGuideOffButton");

        const AUDIO_SETTINGS_KEY = "bbung_hwatu_audio_settings_v1";

        let musicEnabled = false;
        let soundEnabled = true;
        let bgmVolume = 0.22;
        let sfxVolume = 0.80;
        let voiceVolume = 0.80;
        let vibrationEnabled = true;
        let toastTimer = null;
        let lastResultSoundKey = null;
        let latestRenderedGame = null;
        let latestHumanPlayer = null;
        let currentAiDifficulty = null;
        let beginnerTutorialEnabled = false;
        let beginnerTutorialMode = "ADVANCED";
        let tutorialFocusElement = null;

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


        function clamp01(value, fallback = 0) {
            const number = Number(value);

            if (!Number.isFinite(number)) {
                return fallback;
            }

            return Math.min(1, Math.max(0, number));
        }


        function loadAudioSettings() {
            try {
                const raw = localStorage.getItem(AUDIO_SETTINGS_KEY);

                if (raw) {
                    const saved = JSON.parse(raw);

                    musicEnabled = Boolean(saved.musicEnabled);
                    soundEnabled =
                        saved.soundEnabled === undefined
                            ? true
                            : Boolean(saved.soundEnabled);
                    bgmVolume = clamp01(saved.bgmVolume, 0.22);
                    sfxVolume = clamp01(saved.sfxVolume, 0.80);
                    voiceVolume = clamp01(saved.voiceVolume, 0.80);
                    vibrationEnabled =
                        saved.vibrationEnabled === undefined
                            ? true
                            : Boolean(saved.vibrationEnabled);
                }
            } catch (_error) {
                musicEnabled = false;
                soundEnabled = true;
                bgmVolume = 0.22;
                sfxVolume = 0.80;
                voiceVolume = 0.80;
                vibrationEnabled = true;
            }
        }


        function saveAudioSettings() {
            try {
                localStorage.setItem(
                    AUDIO_SETTINGS_KEY,
                    JSON.stringify({
                        musicEnabled,
                        soundEnabled,
                        bgmVolume,
                        sfxVolume,
                        voiceVolume,
                        vibrationEnabled,
                    })
                );
            } catch (_error) {
                // 저장 실패는 게임 진행에 영향 없음.
            }
        }


        function applyAudioSettingsToUi() {
            musicToggle.classList.toggle("is-off", !musicEnabled);
            soundToggle.classList.toggle("is-off", !soundEnabled);

            bgmVolumeInput.value = String(Math.round(bgmVolume * 100));
            sfxVolumeInput.value = String(Math.round(sfxVolume * 100));
            voiceVolumeInput.value = String(Math.round(voiceVolume * 100));
            vibrationToggle.checked = vibrationEnabled;

            bgmVolumeValue.textContent = `${bgmVolumeInput.value}%`;
            sfxVolumeValue.textContent = `${sfxVolumeInput.value}%`;
            voiceVolumeValue.textContent = `${voiceVolumeInput.value}%`;

            lobbyBgm.volume = bgmVolume;
            gameBgm.volume = bgmVolume;

            for (const audio of Object.values(soundEffects)) {
                audio.volume = sfxVolume;
            }
        }


        function readSettingsControls() {
            bgmVolume =
                clamp01(
                    Number(bgmVolumeInput.value) / 100,
                    bgmVolume
                );
            sfxVolume =
                clamp01(
                    Number(sfxVolumeInput.value) / 100,
                    sfxVolume
                );
            voiceVolume =
                clamp01(
                    Number(voiceVolumeInput.value) / 100,
                    voiceVolume
                );
            vibrationEnabled =
                Boolean(vibrationToggle.checked);

            applyAudioSettingsToUi();
        }


        function openSettingsModal() {
            applyAudioSettingsToUi();
            settingsModal.hidden = false;
        }


        function closeSettingsModal() {
            settingsModal.hidden = true;
        }


        function vibratePattern(pattern) {
            if (
                !vibrationEnabled
                || !navigator.vibrate
            ) {
                return;
            }

            try {
                navigator.vibrate(pattern);
            } catch (_error) {
                // 미지원/차단 기기에서는 무시.
            }
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
                audio.volume = sfxVolume;
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
            utterance.volume = voiceVolume;

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

            if (!isGame) {
                hideTutorialGuide();
            }

            if (musicEnabled) {
                const active = isGame ? gameBgm : lobbyBgm;
                const inactive = isGame ? lobbyBgm : gameBgm;

                inactive.pause();
                active.volume = bgmVolume;
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
                registerUsername.value.trim();

            const password =
                registerPassword.value;

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

                authUsername.value = username;
                authPassword.value = "";
                registerPanel.hidden = true;
                authUsername.focus();

                showMessage(
                    "회원가입 완료. 비밀번호를 입력해 로그인해 주세요."
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
                currentAiDifficulty =
                    aiDifficultySelect.value;

                beginnerTutorialEnabled =
                    currentAiDifficulty === "BEGINNER"
                    && Boolean(beginnerTutorialToggle?.checked);

                beginnerTutorialMode =
                    beginnerTutorialLevel?.value
                    || "ADVANCED";

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
                                        currentAuthUser?.nickname
                                        || "플레이어",
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


        function syncBeginnerTutorialOption() {
            if (
                !beginnerTutorialOption
                || !beginnerTutorialToggle
                || !beginnerTutorialLevel
            ) {
                return;
            }

            const isBeginner =
                aiDifficultySelect.value === "BEGINNER";

            beginnerTutorialOption.hidden = !isBeginner;
            beginnerTutorialToggle.disabled = !isBeginner;
            beginnerTutorialLevel.disabled =
                !isBeginner
                || !beginnerTutorialToggle.checked;
        }


        function clearTutorialFocus() {
            if (tutorialFocusElement) {
                tutorialFocusElement.classList.remove("tutorial-focus");
                tutorialFocusElement = null;
            }
        }


        function setTutorialFocus(element) {
            clearTutorialFocus();

            if (!element) {
                return;
            }

            element.classList.add("tutorial-focus");
            tutorialFocusElement = element;
        }


        function hideTutorialGuide() {
            clearTutorialFocus();

            if (tutorialGuide) {
                tutorialGuide.hidden = true;
            }
        }


        function showTutorialGuide(
            title,
            text,
            focusElement = null
        ) {
            if (
                !tutorialGuide
                || !beginnerTutorialEnabled
                || currentGameMode !== "SOLO_AI"
                || currentAiDifficulty !== "BEGINNER"
            ) {
                hideTutorialGuide();
                return;
            }

            tutorialGuideTitle.textContent = title;
            tutorialGuideText.textContent = text;
            tutorialGuide.hidden = false;
            setTutorialFocus(focusElement);
        }


        function isAdvancedTutorial() {
            return beginnerTutorialMode === "ADVANCED";
        }


        function getMonthCountMap(cards) {
            const counts = new Map();

            for (const card of cards || []) {
                const month = Number(card.month);
                counts.set(
                    month,
                    (counts.get(month) || 0) + 1
                );
            }

            return counts;
        }


        function getBombMonths(cards) {
            return Array
                .from(getMonthCountMap(cards).entries())
                .filter(([, count]) => count >= 3)
                .map(([month]) => month)
                .sort((a, b) => a - b);
        }


        function getPairMonths(cards) {
            return Array
                .from(getMonthCountMap(cards).entries())
                .filter(([, count]) => count === 2)
                .map(([month]) => month)
                .sort((a, b) => a - b);
        }


        function getMyActiveDeclaration(game, humanPlayer) {
            if (!game || !humanPlayer) {
                return null;
            }

            const bomb =
                (game.active_bomb_bagaji_declarations || [])
                    .find(
                        declaration =>
                            declaration.player_id
                            === humanPlayer.player_id
                    );

            if (bomb) {
                return {
                    type: "BOMB_BAGAJI",
                    month: bomb.month,
                };
            }

            const general =
                (game.active_bagaji_declarations || [])
                    .find(
                        declaration =>
                            declaration.player_id
                            === humanPlayer.player_id
                    );

            if (general) {
                return {
                    type: "BAGAJI",
                    month: general.month,
                };
            }

            return null;
        }


        function explainRoundResult(game, humanPlayer) {
            if (!humanPlayer) {
                return "이번 판 결과와 점수를 확인하세요.";
            }

            const myRoundScore =
                Number(humanPlayer.round_score || 0);
            const myTotalScore =
                Number(humanPlayer.total_score || 0);

            const winner =
                game.players.find(
                    player =>
                        player.player_id
                        === game.round_winner_id
                );

            const winnerName =
                winner
                    ? winner.nickname
                    : "승자";

            const reason =
                getRoundEndReasonLabel(game);

            return (
                `${winnerName}이(가) 이번 판을 끝냈습니다. `
                + `승리 방식은 ${reason}이고, `
                + `내 이번 판 점수는 ${myRoundScore}점, `
                + `누적 점수는 ${myTotalScore}점입니다. `
                + "이 게임은 누적 점수가 낮을수록 유리합니다."
            );
        }


        function getBestStraightWindow(cards) {
            const uniqueMonths =
                Array.from(
                    new Set(
                        (cards || []).map(
                            card => Number(card.month)
                        )
                    )
                ).sort((a, b) => a - b);

            let best = null;

            for (let start = 1; start <= 7; start += 1) {
                const windowMonths =
                    Array.from(
                        { length: 6 },
                        (_, index) => start + index
                    );

                const matched =
                    windowMonths.filter(
                        month => uniqueMonths.includes(month)
                    );

                const missing =
                    windowMonths.filter(
                        month => !uniqueMonths.includes(month)
                    );

                const candidate = {
                    start,
                    end: start + 5,
                    matched,
                    missing,
                    matchCount: matched.length,
                };

                if (
                    !best
                    || candidate.matchCount > best.matchCount
                    || (
                        candidate.matchCount === best.matchCount
                        && candidate.missing.length < best.missing.length
                    )
                ) {
                    best = candidate;
                }
            }

            return best;
        }


        function getWinningHandHint(cards) {
            if (!Array.isArray(cards) || cards.length === 0) {
                return "";
            }

            const months =
                cards.map(card => Number(card.month));
            const counts = getMonthCountMap(cards);
            const entries =
                Array.from(counts.entries())
                    .sort((a, b) => a[0] - b[0]);

            const pairs =
                entries
                    .filter(([, count]) => count === 2)
                    .map(([month]) => month);

            const triples =
                entries
                    .filter(([, count]) => count === 3)
                    .map(([month]) => month);

            const quads =
                entries
                    .filter(([, count]) => count === 4)
                    .map(([month]) => month);

            const singles =
                entries
                    .filter(([, count]) => count === 1)
                    .map(([month]) => month);

            const sum =
                months.reduce(
                    (total, month) => total + month,
                    0
                );

            const cardsNeeded =
                Math.max(0, 6 - cards.length);

            const stopOptions =
                cards.length === 6
                    ? getAvailableStopOptions(cards)
                    : [];

            if (stopOptions.length) {
                const best =
                    [...stopOptions].sort(
                        (a, b) => a.score - b.score
                    )[0];

                return (
                    `이미 ${getStopLabel(best.type)} STOP 조건이 완성되어 있습니다. `
                    + `예상 점수는 ${best.score}점입니다.`
                );
            }

            if (quads.length) {
                const quadMonth = quads[0];

                if (pairs.length) {
                    return (
                        `현재 ${quadMonth}월 4장과 ${pairs[0]}월 2장이 모여 `
                        + "-100 계열 완성에 매우 가깝습니다. "
                        + "이 조합은 깨지지 않게 유지하는 방향이 좋습니다."
                    );
                }

                if (singles.length) {
                    return (
                        `현재 ${quadMonth}월 4장을 확보했습니다. `
                        + `남은 패에서는 ${singles.join(", ")}월 중 하나를 한 장 더 맞춰 `
                        + "4장+2장 조합을 만드는 방향이 좋습니다."
                    );
                }
            }

            if (triples.length) {
                const tripleMonth = triples[0];

                if (pairs.length) {
                    return (
                        `현재 ${tripleMonth}월 3장 + ${pairs[0]}월 2장입니다. `
                        + `${tripleMonth}월 한 장을 더 모으면 4장+2장 계열을 노릴 수 있으므로 `
                        + `${tripleMonth}월을 가장 우선해서 보는 편이 좋습니다.`
                    );
                }

                return (
                    `현재 ${tripleMonth}월이 3장이라 폭탄 기반이 강합니다. `
                    + `${tripleMonth}월 4번째 패를 노리면서, 다른 월은 2장을 맞춰 `
                    + "4장+2장 STOP 방향을 함께 보는 것이 좋습니다."
                );
            }

            if (pairs.length >= 2) {
                const singletonTarget =
                    singles.length
                        ? singles[0]
                        : null;

                if (singletonTarget !== null) {
                    return (
                        `현재 ${pairs.join(", ")}월이 각각 2장씩 모였습니다. `
                        + `또이또이를 노리기 좋은 형태라서 ${singletonTarget}월 같은 `
                        + "홀수 장 패를 한 장 더 맞춰 세 번째 쌍을 만드는 방향이 좋습니다."
                    );
                }

                return (
                    `현재 ${pairs.join(", ")}월 쌍이 잡혀 있습니다. `
                    + "또이또이 완성을 위해 새로운 쌍 하나를 더 만드는 방향이 좋습니다."
                );
            }

            const straight =
                getBestStraightWindow(cards);

            if (
                straight
                && straight.matchCount >= 4
                && straight.missing.length <= 2
            ) {
                return (
                    `현재 ${straight.start}~${straight.end}월 연속 구간에 `
                    + `${straight.matchCount}장이 들어와 있습니다. `
                    + `빠진 ${straight.missing.join(", ")}월을 모으면 `
                    + "스트레이트 STOP을 노릴 수 있습니다."
                );
            }

            if (pairs.length === 1 && singles.length >= 2) {
                return (
                    `현재 ${pairs[0]}월 한 쌍이 있습니다. `
                    + `${singles.join(", ")}월 중 하나를 한 장 더 맞춰 두 번째 쌍을 만들면 `
                    + "또이또이 쪽으로 발전시키기 좋습니다."
                );
            }

            const remainingSlots =
                Math.max(0, 6 - cards.length);

            const lowSumReachable =
                sum + remainingSlots <= 10;

            if (
                lowSumReachable
                && sum <= Math.max(8, cards.length * 2)
            ) {
                return (
                    `현재 ${cards.length}장 합계가 ${sum}로 낮습니다. `
                    + "1~2월처럼 작은 월을 유지하면 6장 합계 10 이하인 "
                    + "-100 STOP을 노릴 여지가 있습니다."
                );
            }

            const highSumThreshold =
                cards.length >= 5 ? 43 : cards.length * 9;

            if (sum >= highSumThreshold) {
                return (
                    `현재 ${cards.length}장 합계가 ${sum}로 높은 편입니다. `
                    + "10~12월 같은 높은 월을 유지하면 6장 합계 60 이상 STOP을 "
                    + "노리기 좋습니다."
                );
            }

            if (straight && straight.matchCount >= 3) {
                return (
                    `현재 가장 이어지기 좋은 구간은 ${straight.start}~${straight.end}월입니다. `
                    + `특히 ${straight.missing.slice(0, 3).join(", ")}월이 들어오면 `
                    + "스트레이트 방향이 더 좋아집니다."
                );
            }

            if (singles.length) {
                const lowSingles =
                    singles.filter(month => month <= 4);

                if (lowSingles.length >= 2) {
                    return (
                        `아직 뚜렷한 완성형은 없지만 낮은 월 패가 여러 장 있습니다. `
                        + `${lowSingles.join(", ")}월을 너무 쉽게 버리지 말고 `
                        + "낮은 합계 STOP 가능성을 보면서 같은 월 쌍이 생기는지 확인하는 편이 좋습니다."
                    );
                }
            }

            return (
                "아직 한 방향으로 강하게 몰린 패는 아닙니다. "
                + "우선 같은 월 2장을 만드는 쪽을 보고, "
                + "동시에 6개월 연속 구간이 만들어지는지 확인하는 것이 좋습니다."
            );
        }


        function renderBeginnerTutorial(game, humanPlayer) {
            if (
                !beginnerTutorialEnabled
                || currentGameMode !== "SOLO_AI"
                || currentAiDifficulty !== "BEGINNER"
                || !game
                || !humanPlayer
            ) {
                hideTutorialGuide();
                return;
            }

            const advanced = isAdvancedTutorial();

            if (game.status === "DEALER_SELECTION") {
                const mode =
                    game.dealer_selection_mode === "NIGHT"
                    ? "밤"
                    : "낮";

                const rule =
                    mode === "밤"
                    ? "가장 낮은 월을 뽑은 사람이 선입니다."
                    : "가장 높은 월을 뽑은 사람이 선입니다.";

                showTutorialGuide(
                    "먼저 선을 정해요",
                    advanced
                        ? (
                            `현재 한국시간 기준 ${mode} 규칙입니다. `
                            + `${rule} 동점이면 동점자끼리 다시 뽑습니다. `
                            + "이 카드는 본게임 덱과 별개입니다."
                        )
                        : (
                            `현재는 ${mode} 규칙입니다. `
                            + `${rule} 선 정하기 카드를 직접 뽑아보세요.`
                        ),
                    dealerDrawButton
                );
                return;
            }

            if (game.status === "ROUND_END") {
                showTutorialGuide(
                    "이번 판 점수를 확인하세요",
                    advanced
                        ? explainRoundResult(game, humanPlayer)
                        : "이번 판 점수를 확인한 뒤 다음 라운드를 눌러 계속 진행하세요.",
                    nextRoundButton
                );
                return;
            }

            if (game.status === "GAME_END") {
                showTutorialGuide(
                    "게임 종료",
                    advanced
                        ? (
                            `내 최종 누적 점수는 ${Number(humanPlayer.total_score || 0)}점입니다. `
                            + "모든 라운드의 누적 점수가 가장 낮은 플레이어가 최종 승리합니다."
                        )
                        : "모든 라운드가 끝났습니다. 총점이 가장 낮은 플레이어가 승리합니다."
                );
                return;
            }

            if (game.status !== "PLAYING") {
                showTutorialGuide(
                    "게임 준비 중",
                    "게임 상태가 바뀌면 다음 행동을 알려드릴게요."
                );
                return;
            }

            const myDeclaration =
                getMyActiveDeclaration(
                    game,
                    humanPlayer
                );

            if (advanced && myDeclaration) {
                const label =
                    myDeclaration.type === "BOMB_BAGAJI"
                        ? "폭탄 바가지"
                        : "바가지";

                showTutorialGuide(
                    `${label} 선언 중`,
                    `${myDeclaration.month}월을 대상으로 선언 중입니다. `
                    + "선언 조건이 깨지면 자동으로 해제되므로 별도의 철회 버튼은 없습니다.",
                    declarationStatusBadge
                );
                return;
            }

            if (
                advanced
                && bombBagajiPanel
                && bombBagajiPanel.style.display !== "none"
            ) {
                const targetMonth =
                    getBombBagajiTargetMonth(humanPlayer);

                showTutorialGuide(
                    "폭탄 바가지를 선언할 수 있어요",
                    `${targetMonth}월 폭탄 바가지 조건이 만들어졌습니다. `
                    + "선언하면 해당 월을 노리는 상태가 되고, 조건이 깨지면 자동 취소됩니다.",
                    bombBagajiCallButton
                );
                return;
            }

            if (
                advanced
                && generalBagajiPanel
                && generalBagajiPanel.style.display !== "none"
            ) {
                const targetMonth =
                    getGeneralBagajiTargetMonth(humanPlayer);

                showTutorialGuide(
                    "바가지를 선언할 수 있어요",
                    `${targetMonth}월 같은 패 2장을 가진 상태에서 일반 바가지를 선언할 수 있습니다. `
                    + "대상 월을 다른 플레이어가 버리는 상황을 노리는 선언입니다.",
                    generalBagajiCallButton
                );
                return;
            }

            if (
                bbungPanel
                && bbungPanel.style.display !== "none"
            ) {
                const discardedMonth =
                    game.last_discarded_card
                        ? game.last_discarded_card.month
                        : "?";

                showTutorialGuide(
                    "뻥 기회가 왔어요",
                    advanced
                        ? (
                            `상대가 ${discardedMonth}월을 버렸고, `
                            + `내 손에 같은 ${discardedMonth}월 패가 2장 있어 뻥이 가능합니다. `
                            + "뻥을 선언하면 화면에 표시되는 추가 버림 패까지 선택해 진행하세요."
                        )
                        : "상대가 버린 월과 같은 카드 2장이 있으면 뻥을 선언할 수 있습니다.",
                    bbungPanel
                );
                return;
            }

            const isMyTurn =
                game.current_turn_player_id
                === humanPlayer.player_id;

            if (!isMyTurn) {
                if (advanced) {
                    const pairMonths =
                        getPairMonths(humanPlayer.hand);

                    const pairHint =
                        pairMonths.length
                            ? ` 현재 내 손의 같은 월 2장: ${pairMonths.join(", ")}월.`
                            : "";

                    const winningHint =
                        getWinningHandHint(
                            humanPlayer.hand
                        );

                    showTutorialGuide(
                        "상대 차례예요",
                        "상대가 버리는 월을 확인하세요. "
                        + "내 손에 같은 월 2장이 있다면 뻥이나 바가지 판단에 중요합니다."
                        + pairHint
                        + (winningHint
                            ? ` 현재 패 방향: ${winningHint}`
                            : "")
                    );
                } else {
                    showTutorialGuide(
                        "상대 차례예요",
                        "상대가 어떤 월을 버리는지 봐두세요. 같은 월 2장이 있으면 뻥 기회가 생길 수 있습니다."
                    );
                }
                return;
            }

            if (game.turn_phase === "DRAW") {
                if (advanced) {
                    const bombMonths =
                        getBombMonths(humanPlayer.hand);

                    let extra = "";
                    if (bombMonths.length) {
                        extra =
                            ` 현재 ${bombMonths.join(", ")}월은 같은 월 3장 이상이라 폭탄으로 계산될 수 있습니다.`;
                    }

                    const winningHint =
                        getWinningHandHint(
                            humanPlayer.hand
                        );

                    showTutorialGuide(
                        "덱에서 한 장 뽑으세요",
                        "내 턴은 기본적으로 드로우 후 버리기 순서입니다. "
                        + "가운데 카드 뒷면 덱을 눌러 1장을 뽑으세요."
                        + extra
                        + (winningHint
                            ? ` 현재 패 방향: ${winningHint}`
                            : ""),
                        drawDeck
                    );
                } else {
                    showTutorialGuide(
                        "카드를 한 장 뽑아보세요",
                        "가운데 카드 뒷면 덱을 누르면 손패에 카드 1장이 들어옵니다.",
                        drawDeck
                    );
                }
                return;
            }

            if (game.turn_phase === "DISCARD") {
                const stopOptions =
                    getAvailableStopOptions(
                        humanPlayer.hand
                    );

                if (stopOptions.length > 0) {
                    const optionSummary =
                        stopOptions
                            .map(
                                option =>
                                    `${getStopLabel(option.type)} ${option.score}점`
                            )
                            .join(", ");

                    showTutorialGuide(
                        "STOP이 가능해요",
                        advanced
                            ? (
                                `현재 가능한 STOP: ${optionSummary}. `
                                + "STOP 버튼을 누르면 실제 6장 카드와 예상 점수를 비교해 선택할 수 있습니다."
                            )
                            : "현재 손패로 STOP 조건을 만족했습니다. STOP 버튼을 눌러 카드 조합과 예상 점수를 확인해보세요.",
                        stopCallButton
                    );
                    return;
                }

                if (advanced) {
                    const bombMonths =
                        getBombMonths(humanPlayer.hand);
                    const pairMonths =
                        getPairMonths(humanPlayer.hand);

                    const handNotes = [];

                    if (bombMonths.length) {
                        handNotes.push(
                            `${bombMonths.join(", ")}월 폭탄 보유`
                        );
                    }

                    if (pairMonths.length) {
                        handNotes.push(
                            `${pairMonths.join(", ")}월 2장 보유`
                        );
                    }

                    const note =
                        handNotes.length
                            ? ` 현재 패 상태: ${handNotes.join(" / ")}.`
                            : "";

                    const winningHint =
                        getWinningHandHint(
                            humanPlayer.hand
                        );

                    showTutorialGuide(
                        "버릴 카드 1장을 선택하세요",
                        "손패는 월 숫자가 작은 순서대로 정렬되어 있습니다. "
                        + "폭탄 3장은 점수 계산에서 0점 취급되고, 같은 월 2장은 뻥/바가지 기회와 연결될 수 있습니다."
                        + note
                        + (winningHint
                            ? ` 현재 패 방향: ${winningHint}`
                            : ""),
                        myHandElement
                    );
                } else {
                    showTutorialGuide(
                        "카드 한 장을 버리세요",
                        "손패에서 버릴 카드 1장을 누르세요. 손패는 월 숫자가 작은 순서대로 정렬되어 있습니다.",
                        myHandElement
                    );
                }
                return;
            }

            if (game.turn_phase === "REACTION") {
                showTutorialGuide(
                    "반응 단계예요",
                    advanced
                        ? (
                            "다른 플레이어의 버림패에 대해 뻥 같은 인터럽트가 가능한지 확인하는 단계입니다. "
                            + "가능한 선언이 있으면 해당 버튼이 자동으로 나타납니다."
                        )
                        : "뻥이나 다른 선언 기회가 있는지 확인하는 단계입니다."
                );
                return;
            }

            showTutorialGuide(
                "진행 중",
                advanced
                    ? "현재 게임 상태를 기준으로 가능한 행동과 패의 의미를 계속 설명합니다."
                    : "현재 상태에 맞는 버튼이 나타나면 눌러 진행하세요."
            );
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

            latestRenderedGame = game;
            latestHumanPlayer = humanPlayer || null;

            const currentTurnPlayer =
                game.players.find(
                    player =>
                        player.player_id
                        === game.current_turn_player_id
                );

            const totalRounds = game.max_rounds || 20;
            const myTotalScore = humanPlayer ? humanPlayer.total_score : 0;

            gameStatusElement.innerHTML = `
                <div class="status-line status-primary round-hud" aria-label="현재 라운드">
                    <span class="hud-label">라운드</span>
                    <b>${game.round_number}<span class="hud-divider">/</span>${totalRounds}</b>
                </div>

                <div class="status-line score-hud" aria-label="내 총합 점수">
                    <span class="hud-label">내 총점</span>
                    <b>${myTotalScore}</b>
                </div>

                <div class="status-line turn-hud">
                    <span class="hud-label">현재 턴</span>
                    <b>${currentTurnPlayer ? currentTurnPlayer.nickname : "-"}</b>
                </div>

                <div class="status-line status-secondary deck-count-hud">
                    <span class="hud-label">남은 패</span>
                    <b>${game.deck_count}</b>
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

            renderBeginnerTutorial(
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
                declarationStatusBadge.textContent = `폭탄 바가지 선언중`;
                declarationStatusBadge.style.display = "inline-flex";
                return;
            }

            if (general) {
                declarationStatusBadge.textContent = `바가지 선언중`;
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


        function playerDeclarationBadgeMarkup(game, playerId) {
            if (!game || !playerId) {
                return "";
            }

            const bomb = (game.active_bomb_bagaji_declarations || []).find(
                item => item.player_id === playerId
            );
            if (bomb) {
                return `<div class="player-declaration-badge bomb">폭탄 바가지 선언중</div>`;
            }

            const general = (game.active_bagaji_declarations || []).find(
                item => item.player_id === playerId
            );
            if (general) {
                return `<div class="player-declaration-badge general">바가지 선언중</div>`;
            }

            return "";
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
                        <div class="opponent-card-count" aria-label="보유 패 ${player.hand_count}장">
                            <span class="mini-card-back-stack" aria-hidden="true">
                                <i></i><i></i><i></i>
                            </span>
                            <b>×${player.hand_count}</b>
                        </div>
                    </div>
                    <div class="player-score-row">
                        <span>총점 <b>${player.total_score}</b></span>
                        <span>이번 판 ${player.round_score}</span>
                    </div>
                    ${
                        player.bbung_count
                            ? `<div class="bbung-count">뻥 ${player.bbung_count}</div>`
                            : ""
                    }
                    ${playerDeclarationBadgeMarkup(game, player.player_id)}
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

            const sortedHand =
                [...player.hand].sort(
                    (a, b) => {
                        const monthDifference =
                            Number(a.month) - Number(b.month);

                        if (monthDifference !== 0) {
                            return monthDifference;
                        }

                        const aCopy =
                            Number(a.copy_index)
                            || Number(
                                String(a.card_id || "").split(/[-_]/)[1]
                            )
                            || 0;
                        const bCopy =
                            Number(b.copy_index)
                            || Number(
                                String(b.card_id || "").split(/[-_]/)[1]
                            )
                            || 0;

                        return aCopy - bCopy;
                    }
                );

            for (
                const card
                of sortedHand
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
                                card.card_id,
                                button
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


        function getStopOptionReason(stopType, cards) {
            const months = (cards || []).map(card => Number(card.month));
            const counts = new Map();

            for (const month of months) {
                counts.set(month, (counts.get(month) || 0) + 1);
            }

            const values = Array.from(counts.values()).sort((a, b) => a - b);
            const hasFourPlusPair =
                values.length === 2
                && values[0] === 2
                && values[1] === 4;
            const sum = months.reduce((total, month) => total + month, 0);
            const hasLowSum = sum <= 10;

            if (stopType === "STRAIGHT") {
                return "서로 다른 6개월이 연속";
            }
            if (stopType === "HIGH_SUM") {
                return `6장 합계 ${sum}`;
            }
            if (stopType === "TTOI_TTOI") {
                return "같은 월 2장씩 3쌍";
            }
            if (stopType === "MINUS_100") {
                if (hasFourPlusPair && hasLowSum) {
                    return "4장+2장 조합 · 합계 10 이하";
                }
                if (hasFourPlusPair) {
                    return "같은 월 4장 + 다른 같은 월 2장";
                }
                return `6장 합계 ${sum} (10 이하)`;
            }
            if (stopType === "MINUS_200") {
                return "4장+2장 조합 + 합계 10 이하";
            }

            return "";
        }


        function getAvailableStopOptions(cards) {
            if (!Array.isArray(cards) || cards.length !== 6) {
                return [];
            }

            const months = cards.map(card => Number(card.month));
            const sortedMonths = [...months].sort((a, b) => a - b);
            const counts = new Map();

            for (const month of months) {
                counts.set(month, (counts.get(month) || 0) + 1);
            }

            const countValues =
                Array.from(counts.values()).sort((a, b) => a - b);
            const sum =
                months.reduce((total, month) => total + month, 0);

            const isStraight =
                new Set(months).size === 6
                && sortedMonths.every(
                    (month, index) =>
                        month === sortedMonths[0] + index
                );

            const isHighSum = sum >= 60;

            const isTtoiTtoi =
                countValues.length === 3
                && countValues.every(count => count === 2);

            const hasFourPlusPair =
                countValues.length === 2
                && countValues[0] === 2
                && countValues[1] === 4;

            const hasLowSum = sum <= 10;

            const options = [];

            if (isStraight) {
                options.push({
                    type: "STRAIGHT",
                    score: -sum,
                });
            }

            if (isHighSum) {
                options.push({
                    type: "HIGH_SUM",
                    score: -sum,
                });
            }

            if (isTtoiTtoi) {
                options.push({
                    type: "TTOI_TTOI",
                    score: 0,
                });
            }

            if (hasFourPlusPair || hasLowSum) {
                options.push({
                    type: "MINUS_100",
                    score: -100,
                });
            }

            if (hasFourPlusPair && hasLowSum) {
                options.push({
                    type: "MINUS_200",
                    score: -200,
                });
            }

            return options.map(option => ({
                ...option,
                reason: getStopOptionReason(option.type, cards),
                cards,
            }));
        }


        function renderStop(
            game,
            humanPlayer
        ) {
            stopPanel.style.display = "none";
            stopButtons.style.display = "none";
            stopButtons.innerHTML = "";

            if (!humanPlayer) {
                return;
            }

            const availableStopOptions =
                getAvailableStopOptions(humanPlayer.hand);

            const canCallStop =
                game.status === "PLAYING"
                && game.turn_phase === "DISCARD"
                && game.current_turn_player_id === humanPlayer.player_id
                && humanPlayer.hand_count === 6
                && availableStopOptions.length > 0;

            if (!canCallStop) {
                return;
            }

            stopPanel.style.display = "inline-flex";
            stopCallButton.setAttribute(
                "aria-label",
                `STOP 가능 ${availableStopOptions.length}개`
            );
        }


        function createStopCardRow(cards) {
            const row = document.createElement("div");
            row.className = "stop-card-row";

            for (const card of cards) {
                const cardElement = document.createElement("span");
                cardElement.className = "stop-preview-card";
                cardElement.innerHTML = cardMarkup(card);
                row.appendChild(cardElement);
            }

            return row;
        }


        function openStopChoices() {
            stopButtons.innerHTML = "";

            const game = latestRenderedGame;
            const humanPlayer = latestHumanPlayer;

            if (!game || !humanPlayer) {
                stopButtons.style.display = "none";
                return;
            }

            const options = getAvailableStopOptions(humanPlayer.hand);

            if (!options.length) {
                stopButtons.style.display = "none";
                showMessage("현재 선언 가능한 STOP이 없습니다.");
                return;
            }

            const heading = document.createElement("div");
            heading.className = "stop-choice-heading";
            heading.innerHTML = `
                <strong>STOP 선택</strong>
                <span>가능한 패 조합과 예상 점수</span>
            `;
            stopButtons.appendChild(heading);

            const optionList = document.createElement("div");
            optionList.className = "stop-choice-list";

            for (const option of options) {
                const button = document.createElement("button");
                button.type = "button";
                button.className = "stop-choice-button";
                button.setAttribute(
                    "aria-label",
                    `${getStopLabel(option.type)} STOP, 예상 점수 ${option.score}`
                );

                const titleRow = document.createElement("div");
                titleRow.className = "stop-choice-title-row";

                const title = document.createElement("strong");
                title.className = "stop-choice-title";
                title.textContent = `${getStopLabel(option.type)} STOP`;

                const score = document.createElement("b");
                score.className = "stop-choice-score";
                score.textContent = `예상 ${option.score}점`;

                titleRow.append(title, score);

                const reason = document.createElement("div");
                reason.className = "stop-choice-reason";
                reason.textContent = option.reason;

                button.append(
                    titleRow,
                    createStopCardRow(option.cards),
                    reason
                );

                button.addEventListener(
                    "click",
                    () => {
                        stopButtons.style.display = "none";
                        declareStop(option.type);
                    }
                );

                optionList.appendChild(button);
            }

            stopButtons.appendChild(optionList);

            const cancelButton = document.createElement("button");
            cancelButton.type = "button";
            cancelButton.className = "stop-choice-cancel";
            cancelButton.textContent = "취소";

            cancelButton.addEventListener(
                "click",
                () => {
                    stopButtons.style.display = "none";
                }
            );

            stopButtons.appendChild(cancelButton);
            stopButtons.style.display = "block";
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


        function prefersReducedMotion() {
            return (
                window.matchMedia
                && window.matchMedia("(prefers-reduced-motion: reduce)").matches
            );
        }


        async function animateCardFlight({
            card,
            fromElement,
            toElement,
            direction = "draw",
        }) {
            if (
                prefersReducedMotion()
                || !fromElement
                || !toElement
                || !card
            ) {
                return;
            }

            const fromRect = fromElement.getBoundingClientRect();
            const toRect = toElement.getBoundingClientRect();

            if (
                !fromRect.width
                || !fromRect.height
                || !toRect.width
                || !toRect.height
            ) {
                return;
            }

            const targetWidth = Math.max(
                30,
                Math.min(
                    direction === "draw" ? 48 : fromRect.width,
                    58
                )
            );
            const targetHeight = targetWidth * 41 / 25;

            const startX =
                fromRect.left
                + fromRect.width / 2
                - targetWidth / 2;
            const startY =
                fromRect.top
                + fromRect.height / 2
                - targetHeight / 2;

            const endX =
                toRect.left
                + toRect.width / 2
                - targetWidth / 2;
            const endY =
                toRect.top
                + toRect.height / 2
                - targetHeight / 2;

            const ghost = document.createElement("div");
            ghost.className =
                `card-flight card-flight-${direction}`;
            ghost.style.left = `${startX}px`;
            ghost.style.top = `${startY}px`;
            ghost.style.width = `${targetWidth}px`;
            ghost.style.height = `${targetHeight}px`;
            ghost.innerHTML = cardMarkup(card);
            document.body.appendChild(ghost);

            if (!ghost.animate) {
                ghost.style.transform =
                    `translate(${endX - startX}px, ${endY - startY}px)`;
                await new Promise(resolve => setTimeout(resolve, 280));
                ghost.remove();
                return;
            }

            const midX = (endX - startX) * 0.52;
            const midY =
                (endY - startY) * 0.45
                - (direction === "draw" ? 18 : 10);

            const animation = ghost.animate(
                [
                    {
                        transform: "translate(0, 0) scale(.94) rotate(0deg)",
                        opacity: 0.98,
                    },
                    {
                        transform:
                            `translate(${midX}px, ${midY}px) `
                            + "scale(1.03) rotate(-2deg)",
                        opacity: 1,
                        offset: 0.55,
                    },
                    {
                        transform:
                            `translate(${endX - startX}px, ${endY - startY}px) `
                            + "scale(.96) rotate(0deg)",
                        opacity: 0.98,
                    },
                ],
                {
                    duration: direction === "draw" ? 330 : 280,
                    easing: "cubic-bezier(.22,.78,.24,1)",
                    fill: "forwards",
                }
            );

            try {
                await animation.finished;
            } catch (_) {
                // Navigation or a rerender may cancel a cosmetic animation.
            }

            ghost.remove();
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

                    await animateCardFlight({
                        card: data.drawn_card,
                        fromElement: drawDeck,
                        toElement: myHandElement,
                        direction: "draw",
                    });
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
            cardId,
            sourceElement = null
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

                await animateCardFlight({
                    card: data.discarded_card,
                    fromElement: sourceElement,
                    toElement: discardPileElement,
                    direction: "discard",
                });

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
                vibratePattern([80, 50, 120]);

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
                applyAudioSettingsToUi();
                saveAudioSettings();

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
                applyAudioSettingsToUi();
                saveAudioSettings();
            }
        );

        settingsButton.addEventListener(
            "click",
            openSettingsModal
        );

        bgmVolumeInput.addEventListener(
            "input",
            () => {
                bgmVolumeValue.textContent =
                    `${bgmVolumeInput.value}%`;

                bgmVolume =
                    clamp01(
                        Number(bgmVolumeInput.value) / 100,
                        bgmVolume
                    );

                lobbyBgm.volume = bgmVolume;
                gameBgm.volume = bgmVolume;
            }
        );

        sfxVolumeInput.addEventListener(
            "input",
            () => {
                sfxVolumeValue.textContent =
                    `${sfxVolumeInput.value}%`;

                sfxVolume =
                    clamp01(
                        Number(sfxVolumeInput.value) / 100,
                        sfxVolume
                    );

                for (const audio of Object.values(soundEffects)) {
                    audio.volume = sfxVolume;
                }
            }
        );

        voiceVolumeInput.addEventListener(
            "input",
            () => {
                voiceVolumeValue.textContent =
                    `${voiceVolumeInput.value}%`;

                voiceVolume =
                    clamp01(
                        Number(voiceVolumeInput.value) / 100,
                        voiceVolume
                    );
            }
        );

        vibrationToggle.addEventListener(
            "change",
            () => {
                vibrationEnabled =
                    Boolean(vibrationToggle.checked);
            }
        );

        saveSettingsButton.addEventListener(
            "click",
            () => {
                readSettingsControls();
                saveAudioSettings();
                closeSettingsModal();
                showMessage("옵션을 저장했습니다.");
            }
        );

        loadAudioSettings();
        applyAudioSettingsToUi();

        // 인증 검증이 끝나기 전에는 로그인 화면을 기본으로 유지한다.
        // refreshAuth()가 유효한 세션을 확인하면 로비로 전환한다.
        setUiMode("auth");

        loginForm.addEventListener(
            "submit",
            event => {
                event.preventDefault();
                loginAccount();
            }
        );

        registerForm.addEventListener(
            "submit",
            event => {
                event.preventDefault();
                registerAccount();
            }
        );

        showRegisterButton.addEventListener(
            "click",
            () => {
                registerPanel.hidden = false;
                registerUsername.value = authUsername.value.trim();
                registerUsername.focus();
            }
        );

        showLoginButton.addEventListener(
            "click",
            () => {
                registerPanel.hidden = true;
                authUsername.focus();
            }
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

        aiDifficultySelect
            .addEventListener(
                "change",
                syncBeginnerTutorialOption
            );

        beginnerTutorialToggle
            .addEventListener(
                "change",
                syncBeginnerTutorialOption
            );

        beginnerTutorialLevel
            .addEventListener(
                "change",
                () => {
                    beginnerTutorialMode =
                        beginnerTutorialLevel.value;
                }
            );

        tutorialGuideOffButton
            .addEventListener(
                "click",
                () => {
                    beginnerTutorialEnabled = false;
                    hideTutorialGuide();

                    if (beginnerTutorialToggle) {
                        beginnerTutorialToggle.checked = false;
                    }

                    showMessage("초보 게임 안내를 껐습니다.");
                }
            );

        syncBeginnerTutorialOption();

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
