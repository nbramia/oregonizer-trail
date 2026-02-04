        // Helper function to add CSRF token to fetch requests
        function fetchWithCSRF(url, options = {}) {
            // Add CSRF token to headers if this is a POST/PUT/DELETE request
            if (options.method && options.method !== 'GET') {
                options.headers = options.headers || {};
                options.headers['X-CSRFToken'] = csrfToken;
            }
            return fetch(url, options);
        }

        let gameState = "initial";  // Possible states: "initial", "mid", "win", "failure", "restart"
        let turnIncremented = false; // Track if the turn has been incremented

        // Handle the login form submission
        async function handleLogin(event) {
            event.preventDefault();
            const form = event.target;
            const formData = new FormData(form);
            const response = await fetchWithCSRF('/', {
                method: 'POST',
                body: formData
            });

            if (response.ok) {
                const data = await response.json();
                if (data.authenticated) {
                    document.body.setAttribute('data-email', data.email);  // Update email attribute
                    document.getElementById('loginModal').style.display = 'none';
                    document.getElementById('email').value = '';
                    document.getElementById('password').value = '';
                    await resetGame();
                    await setDifficulty('Normal');
                    // Load modes first to get default mode, then set it
                    if (!defaultMode) {
                        await loadAvailableModes();
                    } else {
                        await setMode(defaultMode);
                    }
                    document.getElementById('overlay').style.display = 'flex';
                } else {
                    alert('Invalid email or password');
                }
            } else {
                alert('Error during login. Please try again.');
            }
        }

        // Dismiss settings modal
        function dismissSettingsModal() {
            const settingsModal = document.getElementById('settingsModal');
            if (settingsModal) {
                settingsModal.classList.add('hidden');
                settingsModal.style.display = 'none'; // Ensure it is hidden
                console.log('Settings modal hidden');
            } else {
                console.error('Settings modal not found');
            }
        }

        // Tab switching logic
        function openTab(evt, tabName) {
            // Hide all tab contents
            var tabcontent = document.getElementsByClassName("tab-content");
            for (var i = 0; i < tabcontent.length; i++) {
                tabcontent[i].style.display = "none";
            }

            // Remove active class from all tab buttons
            var tablinks = document.getElementsByClassName("tab-button");
            for (var i = 0; i < tablinks.length; i++) {
                tablinks[i].className = tablinks[i].className.replace(" active", "");
            }

            // Show the current tab and add active class to the button
            document.getElementById(tabName).style.display = "block";
            evt.currentTarget.className += " active";

            // Fetch leaderboard data if the Leaderboard tab is opened
            if (tabName === 'Leaderboard') {
                fetchLeaderboard();
            }
        }

        // Fetch user info and leaderboard data
        async function fetchUserInfo() {
            try {
                const response = await fetchWithCSRF('/get_user_info');
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                const data = await response.json();
                document.getElementById('current_email').innerText = `User: ${data.email}`;
                document.getElementById('games_played').innerText = `Games Played: ${data.games_played}`;
                document.getElementById('high_score').innerText = `High Score: ${data.high_score}`;
            } catch (error) {
                console.error('Error fetching user info: ', error);
            }
        }

        async function fetchLeaderboard() {
            try {
                const response = await fetchWithCSRF('/get_leaderboard');
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                const leaderboard = await response.json();
                console.log('Fetched leaderboard data:', leaderboard);
                const leaderboardBody = document.getElementById('leaderboardBody');
                leaderboardBody.innerHTML = leaderboard.map((entry, index) => {
                    const trimmedEmail = entry.email.split('@')[0];
                    return `
                        <tr>
                            <td>${trimmedEmail}</td>
                            <td>${entry.high_score}</td>
                        </tr>
                    `;
                }).join('');
            } catch (error) {
                console.error('Error fetching leaderboard: ', error);
            }
        }

        document.getElementById('scenarioType').addEventListener('change', function() {
            const type = this.value;
            const decisionFields = document.getElementById('decisionResponseFields');
            const decisionMetricsFields = document.getElementById('decisionMetricsFields');
            
            if (type === 'decision') {
                decisionFields.classList.remove('hidden');
                decisionMetricsFields.classList.remove('hidden');
            } else {
                decisionFields.classList.add('hidden');
                decisionMetricsFields.classList.add('hidden');
            }
        });

        async function renderScenarioMetricFields(mode) {
            console.log(`Rendering scenario metric fields for mode: ${mode}`);
            try {
                // Fetch metrics for the selected mode
                const response = await fetchWithCSRF(`/get_mode_metrics?mode=${encodeURIComponent(mode)}`);
                if (!response.ok) throw new Error('Failed to fetch mode metrics');

                const data = await response.json();
                const metrics = data.metrics;
                console.log('Metrics for scenario form:', metrics);

                // Render decision scenario metrics (Yes/No)
                const yesMetricsDiv = document.getElementById('yesMetrics');
                const noMetricsDiv = document.getElementById('noMetrics');
                yesMetricsDiv.innerHTML = '';
                noMetricsDiv.innerHTML = '';

                metrics.forEach(metric => {
                    // Yes metrics
                    const yesFieldHTML = `
                        <div class="form-group mb-2">
                            <label for="${metric.key}Yes">Effect on ${metric.display} (-30 to 30):</label>
                            <input type="number" id="${metric.key}Yes" class="form-control px-2 text-black w-1/12" style="border-radius: 0; border: 2px solid var(--phosphor-green);" value="0">
                            <small id="${metric.key}YesError" class="text-red-500 hidden">Value must be between -30 and 30.</small>
                        </div>
                    `;
                    yesMetricsDiv.innerHTML += yesFieldHTML;

                    // No metrics
                    const noFieldHTML = `
                        <div class="form-group mb-2">
                            <label for="${metric.key}No">Effect on ${metric.display} (-30 to 30):</label>
                            <input type="number" id="${metric.key}No" class="form-control px-2 text-black w-1/12" style="border-radius: 0; border: 2px solid var(--phosphor-green);" value="0">
                            <small id="${metric.key}NoError" class="text-red-500 hidden">Value must be between -30 and 30.</small>
                        </div>
                    `;
                    noMetricsDiv.innerHTML += noFieldHTML;
                });

                // Render informational scenario metrics
                const infoMetricsDiv = document.getElementById('informationalMetricsFields');
                infoMetricsDiv.innerHTML = '';

                metrics.forEach(metric => {
                    const fieldHTML = `
                        <div class="form-group mb-2">
                            <label for="${metric.key}">Effect on ${metric.display} (-30 to 30):</label>
                            <input type="number" id="${metric.key}" class="form-control px-2 text-black w-1/12" style="border-radius: 0; border: 2px solid var(--phosphor-green);" value="0">
                            <small id="${metric.key}Error" class="text-red-500 hidden">Value must be between -30 and 30.</small>
                        </div>
                    `;
                    infoMetricsDiv.innerHTML += fieldHTML;
                });

                console.log('Scenario metric fields rendered successfully');
            } catch (error) {
                console.error('Error rendering scenario metric fields:', error);
            }
        }

        function openCreateScenarioModal() {
            fetchWithCSRF('/get_modes')
                .then(response => response.json())
                .then(data => {
                    const modeSelect = document.getElementById('scenarioMode');
                    modeSelect.innerHTML = ''; // Clear existing options

                    data.modes.forEach(mode => {
                        const option = document.createElement('option');
                        option.value = mode;
                        option.textContent = mode;
                        // Set Movement Labs as default
                        if (mode === 'Movement Labs') {
                            option.selected = true;
                        }
                        modeSelect.appendChild(option);
                    });

                    // Add event listener to mode selector to update metrics when mode changes
                    modeSelect.addEventListener('change', function() {
                        if (this.value) {
                            renderScenarioMetricFields(this.value);
                        }
                    });

                    // Initialize metrics for default mode (Movement Labs)
                    if (modeSelect.value) {
                        renderScenarioMetricFields(modeSelect.value);
                    }

                    document.getElementById('createScenarioModal').classList.remove('hidden');
                })
                .catch(error => {
                    console.error('Error fetching modes:', error);
                });
        }

        function closeCreateScenarioModal() {
            document.getElementById('createScenarioModal').classList.add('hidden');
        }

        function validateField(input, condition, errorElementId) {
            const errorElement = document.getElementById(errorElementId);
            if (condition) {
                errorElement.classList.add('hidden');
                console.log(`${input.id} is valid.`);
                return true;
            } else {
                errorElement.classList.remove('hidden');
                console.log(`${input.id} is invalid.`);
                return false;
            }
        }

        function validateForm() {
            const name = document.getElementById('scenarioName').value.trim().toLowerCase().replace(/\s+/g, '_');
            const mode = document.getElementById('scenarioMode').value;
            const type = document.getElementById('scenarioType').value;
            const text = document.getElementById('scenarioText').value.trim();

            console.log(`Validating form with values:
                name=${name},
                mode=${mode},
                type=${type},
                text=${text}`);

            const nameValid = validateField(name, /^[a-z0-9_]+$/.test(name), 'scenarioNameError');
            const modeValid = validateField(mode, mode !== '', 'scenarioModeError');
            const typeValid = validateField(type, type === 'decision' || type === 'informational', 'scenarioTypeError');
            const textValid = validateField(text, text !== '', 'scenarioTextError');

            let metricsValid = true;
            let responsesValid = true;

            // Validate metrics dynamically based on current mode
            if (type === 'informational') {
                // Validate each metric for informational scenarios
                currentModeMetrics.forEach(metric => {
                    const element = document.getElementById(metric.key);
                    if (element) {
                        const value = parseInt(element.value);
                        const isValid = !isNaN(value) && value >= -30 && value <= 30;
                        const errorId = `${metric.key}Error`;
                        const fieldValid = validateField(value, isValid, errorId);
                        metricsValid = metricsValid && fieldValid;
                        console.log(`${metric.key}=${value}, valid=${fieldValid}`);
                    }
                });
            }

            if (type === 'decision') {
                // Validate responses
                const yesResponse = document.getElementById('yesResponse').value.trim();
                const noResponse = document.getElementById('noResponse').value.trim();
                responsesValid = validateField(yesResponse, yesResponse !== '', 'yesResponseError') &&
                                validateField(noResponse, noResponse !== '', 'noResponseError');

                // Validate metrics for both Yes and No options
                currentModeMetrics.forEach(metric => {
                    const yesElement = document.getElementById(`${metric.key}Yes`);
                    const noElement = document.getElementById(`${metric.key}No`);

                    if (yesElement) {
                        const yesValue = parseInt(yesElement.value);
                        const yesValid = !isNaN(yesValue) && yesValue >= -30 && yesValue <= 30;
                        const yesFieldValid = validateField(yesValue, yesValid, `${metric.key}YesError`);
                        metricsValid = metricsValid && yesFieldValid;
                        console.log(`${metric.key}Yes=${yesValue}, valid=${yesFieldValid}`);
                    }

                    if (noElement) {
                        const noValue = parseInt(noElement.value);
                        const noValid = !isNaN(noValue) && noValue >= -30 && noValue <= 30;
                        const noFieldValid = validateField(noValue, noValid, `${metric.key}NoError`);
                        metricsValid = metricsValid && noFieldValid;
                        console.log(`${metric.key}No=${noValue}, valid=${noFieldValid}`);
                    }
                });
            }

            const isFormValid = nameValid && modeValid && typeValid && textValid && responsesValid && metricsValid;
            console.log(`isFormValid=${isFormValid}`);
            return isFormValid;
        }


        function toggleScenarioFields() {
            const type = document.getElementById('scenarioType').value;
            const decisionFields = document.getElementById('decisionResponseFields');
            const informationalFields = document.getElementById('informationalMetricsFields');

            const decisionInputs = decisionFields.querySelectorAll('input, textarea');
            const informationalInputs = informationalFields.querySelectorAll('input');

            if (type === 'decision') {
                decisionFields.classList.remove('hidden');
                informationalFields.classList.add('hidden');

                // Make decision inputs required and remove required from informational inputs
                decisionInputs.forEach(input => input.required = true);
                informationalInputs.forEach(input => input.required = false);
            } else {
                decisionFields.classList.add('hidden');
                informationalFields.classList.remove('hidden');

                // Make informational inputs required and remove required from decision inputs
                informationalInputs.forEach(input => input.required = true);
                decisionInputs.forEach(input => input.required = false);
            }
        }

        document.addEventListener('DOMContentLoaded', function() {
            const scenarioType = document.getElementById('scenarioType');
            const decisionFields = document.getElementById('decisionResponseFields');
            const decisionMetricsFields = document.getElementById('decisionMetricsFields');
            const informationalMetricsFields = document.getElementById('informationalMetricsFields');
            const scenarioNameError = document.getElementById('scenarioNameError');
            const scenarioText = document.getElementById('scenarioText');

            scenarioType.addEventListener('change', function() {
                if (this.value === 'decision') {
                    decisionFields.classList.remove('hidden');
                    decisionMetricsFields.classList.remove('hidden');
                    informationalMetricsFields.classList.add('hidden');
                    scenarioText.placeholder = "What is the difficult choice to be made?";

                    // Set required attribute for decision inputs and remove from informational inputs
                    setRequiredAttributes(decisionFields, true);
                    setRequiredAttributes(decisionMetricsFields, true);
                    setRequiredAttributes(informationalMetricsFields, false);
                } else {
                    decisionFields.classList.add('hidden');
                    decisionMetricsFields.classList.add('hidden');
                    informationalMetricsFields.classList.remove('hidden');
                    scenarioText.placeholder = "What happened?";

                    // Set required attribute for informational inputs and remove from decision inputs
                    setRequiredAttributes(decisionFields, false);
                    setRequiredAttributes(decisionMetricsFields, false);
                    setRequiredAttributes(informationalMetricsFields, true);
                }
            });

            document.getElementById('createScenarioForm').addEventListener('submit', async function(event) {
                event.preventDefault();

                const name = document.getElementById('scenarioName').value.trim().toLowerCase().replace(/\s+/g, '_');
                const mode = document.getElementById('scenarioMode').value;
                const type = document.getElementById('scenarioType').value;
                const text = document.getElementById('scenarioText').value.trim();

                // Basic validation
                if (!name || !mode || !type || !text) {
                    alert('Please fill in all required fields');
                    return;
                }

                // Fetch current mode's metrics to know what to collect
                const metricsResponse = await fetchWithCSRF(`/get_mode_metrics?mode=${encodeURIComponent(mode)}`);
                const metricsData = await metricsResponse.json();
                const modeMetrics = metricsData.metrics;

                let metrics = {};
                if (type === 'decision') {
                    metrics.yes = {};
                    metrics.no = {};

                    // Collect all metrics for Yes and No
                    modeMetrics.forEach(metric => {
                        const yesValue = parseInt(document.getElementById(`${metric.key}Yes`).value) || 0;
                        const noValue = parseInt(document.getElementById(`${metric.key}No`).value) || 0;

                        metrics.yes[metric.key] = yesValue;
                        metrics.no[metric.key] = noValue;
                    });
                } else if (type === 'informational') {
                    // Collect all metrics for informational scenario
                    modeMetrics.forEach(metric => {
                        const value = parseInt(document.getElementById(metric.key).value) || 0;
                        metrics[metric.key] = value;
                    });
                }

                let response = null;
                if (type === 'decision') {
                    const yesResponse = document.getElementById('yesResponse').value.trim();
                    const noResponse = document.getElementById('noResponse').value.trim();
                    response = {
                        yes: yesResponse,
                        no: noResponse
                    };
                }

                console.log("Submitting form with data:", {
                    name: name,
                    mode: mode,
                    type: type,
                    text: text,
                    metrics: metrics,
                    response: response
                });

                fetchWithCSRF('/create_scenario', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        name: name,
                        mode: mode,
                        type: type,
                        text: text,
                        metrics: metrics,  // Send the metrics in the correct format
                        response: response
                    })
                }).then(response => {
                    console.log("Fetch response:", response);
                    if (response.ok) {
                        return response.json();
                    } else {
                        return response.json().then(error => { throw new Error(error.error); });
                    }
                }).then(data => {
                    console.log("Scenario created successfully:", data);
                    alert('Scenario created successfully.');
                    closeCreateScenarioModal();
                }).catch(error => {
                    console.error("Error creating scenario:", error);
                    if (error.message === 'A scenario with this name already exists.') {
                        scenarioNameError.textContent = error.message;
                        scenarioNameError.classList.remove('hidden');
                    } else {
                        alert('Failed to create scenario.');
                    }
                });
            });

            // Helper function to set the required attribute on all inputs in a container
            function setRequiredAttributes(container, required) {
                const inputs = container.querySelectorAll('input, textarea');
                inputs.forEach(input => input.required = required);
            }
        });

        // Logout function
        async function logout() {
            console.log('Logging out...');
            const response = await fetchWithCSRF('/logout', { method: 'POST' });
            if (response.ok) {
                console.log('Logout successful');
                await resetGame();
                document.getElementById('settingsModal').classList.add('hidden');
                document.getElementById('settingsModal').style.display = 'none'; // Ensure the modal is hidden
                document.getElementById('loginModal').style.display = 'flex';
            } else {
                alert('Logout failed');
            }
        }

        async function setDifficulty(difficulty) {
            console.log(`Setting difficulty to ${difficulty}`);
            const response = await fetchWithCSRF('/set_difficulty', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ difficulty })
            });
            const data = await response.json();
            console.log(data.message);
            updateMetrics(data.metrics); // Update the initial metrics based on difficulty

            // Set the selected value in the dropdown
            document.getElementById('difficulty_selector_settings').value = difficulty;
            document.getElementById('difficulty_selector_overlay').value = difficulty;

            // Update the displayed current difficulty
            document.getElementById('current_difficulty').innerText = difficulty;
            document.getElementById('current_difficulty_bottom').innerText = difficulty;

            // Reset the game whenever the difficulty is changed
            await resetGame();
        }

        async function loadAvailableModes() {
            console.log('Loading available modes...');
            try {
                const response = await fetchWithCSRF('/get_modes', {
                    method: 'GET',
                    headers: {
                        'Content-Type': 'application/json'
                    }
                });

                if (!response.ok) {
                    console.error('Failed to fetch modes');
                    return;
                }

                const data = await response.json();
                const modes = data.modes;
                defaultMode = data.default_mode || (modes.length > 0 ? modes[0] : null);
                console.log('Available modes:', modes);
                console.log('Default mode:', defaultMode);

                // Populate both mode selectors
                const overlaySelect = document.getElementById('mode_selector_overlay');
                const settingsSelect = document.getElementById('mode_selector_settings');

                // Clear existing options
                overlaySelect.innerHTML = '';
                settingsSelect.innerHTML = '';

                // Add options for each available mode
                modes.forEach(mode => {
                    const overlayOption = document.createElement('option');
                    overlayOption.value = mode;
                    overlayOption.textContent = mode;
                    if (mode === defaultMode) {
                        overlayOption.selected = true;
                    }
                    overlaySelect.appendChild(overlayOption);

                    const settingsOption = document.createElement('option');
                    settingsOption.value = mode;
                    settingsOption.textContent = mode;
                    if (mode === defaultMode) {
                        settingsOption.selected = true;
                    }
                    settingsSelect.appendChild(settingsOption);
                });

                // Set default mode and ensure metrics are loaded
                if (defaultMode) {
                    // Load metrics first for the default mode
                    await loadModeMetrics(defaultMode);
                    // Then set the mode (which will also trigger another loadModeMetrics, but that's OK)
                    await setMode(defaultMode);
                }
            } catch (error) {
                console.error('Error loading modes:', error);
            }
        }

        // Global variable to store current mode's metrics configuration
        let currentModeMetrics = [];
        let defaultMode = null;  // Will be set from server

        async function loadModeMetrics(mode) {
            console.log(`Loading metrics for mode: ${mode}`);
            try {
                const response = await fetchWithCSRF(`/get_mode_metrics?mode=${encodeURIComponent(mode)}`);
                if (!response.ok) {
                    throw new Error('Failed to fetch mode metrics');
                }
                const data = await response.json();
                currentModeMetrics = data.metrics;
                console.log('Loaded mode metrics:', currentModeMetrics);

                // Render the metric bars dynamically
                renderMetricBars();

                return currentModeMetrics;
            } catch (error) {
                console.error('Error loading mode metrics:', error);
                // Fallback to default metrics
                currentModeMetrics = [
                    {key: 'staff_retention', display: 'Staff Retention'},
                    {key: 'partner_retention', display: 'Partner Retention'},
                    {key: 'partner_growth', display: 'Partner Growth'},
                    {key: 'tech_debt', display: 'Tech Debt'}
                ];
                renderMetricBars();
                return currentModeMetrics;
            }
        }

        function renderMetricBars() {
            console.log('Rendering metric bars...');
            const container = document.getElementById('metrics-container');
            container.innerHTML = ''; // Clear existing bars

            currentModeMetrics.forEach(metric => {
                const metricDiv = document.createElement('div');
                metricDiv.className = 'metric-item mb-1';
                metricDiv.innerHTML = `
                    <span class="metric-label">${metric.display}:</span>
                    <div class="health-bar-container">
                        <div class="health-bar" id="${metric.key}_bar"></div>
                    </div>
                `;
                container.appendChild(metricDiv);
            });

            console.log('Metric bars rendered');
        }

        async function setMode(mode) {
            console.log(`Setting mode to ${mode}`);
            try {
                const response = await fetchWithCSRF('/set_mode', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ mode })
                });

                if (!response.ok) {
                    throw new Error('Failed to set mode');
                }

                const data = await response.json();
                console.log(data.message);

                // Load metrics configuration for this mode
                await loadModeMetrics(mode);

                // Update the initial metrics based on mode
                updateMetrics(data.metrics);

                // Set the selected value in the dropdown
                document.getElementById('mode_selector_overlay').value = mode;
                document.getElementById('mode_selector_settings').value = mode;

                // Update the displayed current mode
                document.getElementById('current_mode').innerText = mode;
                document.getElementById('current_mode_bottom').innerText = mode;

                // Reset the game whenever the mode is changed
                await resetGame();
            } catch (error) {
                console.error('Error setting mode:', error);
            }
        }

        function displayScenario(data) {
            console.log(`Displaying scenario: ${data.scenario}`);
            let scenarioText = data.scenario_text.replace(/\n/g, '<br>');
            if (data.is_community) {
                scenarioText = `<b>Community-submitted scenario:</b><br><br>${scenarioText}`;
            }
            const scenarioTextElement = document.getElementById('scenario_text');
            scenarioTextElement.innerHTML = scenarioText;
            scenarioTextElement.dataset.scenario = data.scenario_id; // Set the scenario ID here
            console.log(`Set scenario ID in dataset: ${scenarioTextElement.dataset.scenario}`);
            document.getElementById('scenario').style.display = 'block';
            document.getElementById('scenario').classList.remove('hidden'); // Ensure it's visible
            document.getElementById('messages').style.display = 'none';

            // Show Yes/No buttons if it's a decision scenario
            if (data.is_decision) {
                console.log("Displaying decision scenario");
                document.getElementById('yes_button').classList.remove('hidden');
                document.getElementById('no_button').classList.remove('hidden');
                document.getElementById('next_button_scenario').classList.add('hidden');
                document.getElementById('next_button_messages').classList.add('hidden'); // Also hide the messages next button
            } else {
                console.log("Displaying non-decision scenario");
                document.getElementById('yes_button').classList.add('hidden');
                document.getElementById('no_button').classList.add('hidden');
                document.getElementById('next_button_scenario').classList.remove('hidden');
            }
        }


        async function nextTurn(isFirstTurn = false) {
            console.log("Next turn...");
            turnIncremented = !isFirstTurn; // Only set to true if it's not the first turn

            // Clear the messages and scenario before proceeding to the next turn
            document.getElementById('messages').style.display = 'none';
            document.getElementById('scenario').style.display = 'block';
            document.getElementById('messages').innerHTML = '';
            document.getElementById('scenario_text').innerText = '';

            if (gameState !== "failure") {
                document.getElementById('next_button_messages').classList.add('hidden');
                document.getElementById('next_button_scenario').classList.add('hidden');
            }

            try {
                const response = await fetchWithCSRF('/next_turn', {
                    method: 'POST'
                });
                const text = await response.text();
                console.log("Next turn response text:", text);

                // Check if the response is JSON
                let data;
                try {
                    data = JSON.parse(text);
                } catch (error) {
                    console.error("Error parsing JSON:", error);
                    return;
                }

                // Increment the turn number only if it's not the first turn and it hasn't been incremented yet
                if (!isFirstTurn && !turnIncremented) {
                    data.metrics.turns_survived++;
                    turnIncremented = true;
                }

                console.log("Updating metrics before handling failure state");
                updateMetrics(data.metrics); // Ensure metrics are updated first

                if (data.status_message) {
                    if (data.status_message.includes("Failure")) {
                        console.log("Failure state detected. Metrics:", data.metrics);
                        gameState = "failure"; // Set game state to failure
                        updateMetrics(data.metrics); // Ensure metrics are updated in failure state
                        displayStatusMessage(data.status_message);
                        endGame();
                    } else {
                        displayStatusMessage(data.status_message);
                        if (data.status_message.startsWith("Congratulations")) {
                            gameState = "win";
                            endGame();
                        }
                    }
                } else {
                    console.log("Scenario data:", data);
                    displayScenario(data);
                }
            } catch (error) {
                console.error("Error in nextTurn:", error);
            }
        }
        async function startGame() {
            console.log("Starting game...");
            await resetGame();  // Ensure game is reset before starting
            gameState = "mid";
            document.getElementById('start_button').innerText = 'Restart Game';
            document.getElementById('restart_button_bottom').innerText = 'Restart Game';
                document.getElementById('restart_button_bottom').classList.add('inactive');
                document.getElementById('restart_button_bottom').classList.remove('button');
                document.getElementById('start_button').classList.add('inactive');
                document.getElementById('start_button').classList.remove('button');

            // Handle visibility based on screen width
            if (window.innerWidth <= 768) {
                document.getElementById('start_button').classList.add('hidden');
                document.getElementById('restart_button_bottom').classList.remove('hidden');
            } else {
                document.getElementById('start_button').classList.remove('hidden');
                document.getElementById('restart_button_bottom').classList.add('hidden');
            }

            document.getElementById('welcome_gif').classList.add('hidden'); // Hide the welcome GIF
            await nextTurn(true);  // Fetch the first turn without incrementing the turn count

            // Dismiss the Settings modal if it's visible
            const settingsModal = document.getElementById('settingsModal');
            if (settingsModal) {
                settingsModal.classList.add('hidden');
                settingsModal.style.display = 'none'; // Ensure it is hidden
                console.log('Settings modal hidden');
            }
        }

        async function resetGame() {
            console.log("Resetting game...");
            try {
                const response = await fetchWithCSRF('/reset_game', {
                    method: 'POST'
                });
                const text = await response.text();
                console.log("Response text from /reset_game:", text);

                // Check if the response is JSON
                let data;
                try {
                    data = JSON.parse(text);
                } catch (error) {
                    console.error("Error parsing JSON:", error);
                    return;
                }

                data.metrics.turns_survived = 0;  // Ensure turn count starts at 0
                updateMetrics(data.metrics);

                // Clear the scenario and messages
                document.getElementById('messages').style.display = 'none';
                document.getElementById('messages').innerHTML = '';
                document.getElementById('scenario').style.display = 'none';
                document.getElementById('scenario_text').innerText = '';

                if (gameState !== "initial") {
                    updateMessages(["Game has been reset."]);
                } else {
                    updateMessages([]); // Clear messages on initial start
                }

                document.getElementById('start_button').innerText = 'Start Game';
                document.getElementById('restart_button_bottom').innerText = 'Start Game';
                
                // Handle visibility based on screen width
                if (window.innerWidth <= 768) {
                    document.getElementById('start_button').classList.remove('hidden');
                    document.getElementById('restart_button_bottom').classList.add('hidden');
                } else {
                    document.getElementById('start_button').classList.remove('hidden');
                    document.getElementById('restart_button_bottom').classList.add('hidden');
                }

                document.getElementById('yes_button').classList.add('hidden');
                document.getElementById('no_button').classList.add('hidden');
                document.getElementById('next_button_scenario').classList.add('hidden');
                document.getElementById('next_button_messages').classList.add('hidden');

                // Hide the GIFs and image when the game restarts
                document.getElementById('win_gif').classList.add('hidden');
                document.getElementById('failure_image').classList.add('hidden');

                // Show the welcome GIF
                document.getElementById('welcome_gif').classList.remove('hidden');

                gameState = "initial";
            } catch (error) {
                console.error("Error resetting game:", error);
            }
        }

        // Add event listener for window resize to manage button visibility
        window.addEventListener('resize', function() {
            if (gameState === "mid") {
                if (window.innerWidth <= 768) {
                    document.getElementById('start_button').classList.add('hidden');
                    document.getElementById('restart_button_bottom').classList.remove('hidden');
                } else {
                    document.getElementById('start_button').classList.remove('hidden');
                    document.getElementById('restart_button_bottom').classList.add('hidden');
                }
            } else {
                if (window.innerWidth <= 768) {
                    document.getElementById('start_button').classList.remove('hidden');
                    document.getElementById('restart_button_bottom').classList.add('hidden');
                } else {
                    document.getElementById('start_button').classList.remove('hidden');
                    document.getElementById('restart_button_bottom').classList.add('hidden');
                }
            }
        });

        function updateMessages(messages) {
            console.log("Updating messages...", messages);
            const messagesDiv = document.getElementById('messages');
            messagesDiv.innerHTML = messages.map(msg => `<p>${msg}</p>`).join('');
        }

        async function handleScenario(action) {
            console.log(`Handling scenario action: ${action}`);
            const scenario = document.getElementById('scenario_text').dataset.scenario;
            const scenarioId = parseInt(scenario, 10); // Ensure it's an integer
            console.log(`Scenario ID: ${scenarioId}`);

            try {
                const response = await fetchWithCSRF('/handle_scenario', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ scenario: scenarioId, action }) // Pass the scenario ID as an integer
                });

                console.log(`Response status: ${response.status}`);

                if (!response.ok) {
                    const errorData = await response.json();
                    console.error(`Server responded with an error: ${errorData.error}`);
                    throw new Error(errorData.error);
                }

                const data = await response.json();
                console.log(`Response data: ${JSON.stringify(data)}`);

                if (data.error) {
                    throw new Error(data.error);
                }

                updateMetrics(data.metrics);
                updateMessages([data.message]);

                document.getElementById('messages').style.display = 'block';
                document.getElementById('scenario').style.display = 'none';

                // Update scenario text to display response
                document.getElementById('scenario_text').innerText = data.message;

                if (data.status_message) {
                    displayStatusMessage(data.status_message);
                    if (data.status_message.startsWith("Congratulations")) {
                        gameState = "win";
                        endGame();
                    } else if (data.status_message.includes("Failure")) {
                        gameState = "failure";
                        endGame();
                    }
                } else if (data.scenario) {
                    displayScenario(data);
                } else {
                    document.getElementById('scenario_text').innerText = '';
                    document.getElementById('next_button_messages').classList.remove('hidden');
                    document.getElementById('yes_button').classList.add('hidden');
                    document.getElementById('no_button').classList.add('hidden');
                }
            } catch (error) {
                console.error("Error handling scenario:", error);
                alert("An error occurred while handling the scenario. Please check the console for details.");
            }
        }


        async function setIncludeCommunityScenarios(include) {
            try {
                const response = await fetchWithCSRF('/set_include_community_scenarios', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ include })
                });

                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                const data = await response.json();
                console.log('Include community scenarios updated:', data);
                
                // Restart the game
                await resetGame();

            } catch (error) {
                console.error('Error setting include community scenarios:', error);
            }
        }


        function updateMetrics(metrics) {
            console.log("Updating metrics...", metrics);
            console.log(`Turns Survived: ${metrics.turns_survived}`);

            // Update turns survived
            document.getElementById('turns_survived').innerText = metrics.turns_survived;

            // Update all metric bars dynamically based on currentModeMetrics
            if (currentModeMetrics && currentModeMetrics.length > 0) {
                currentModeMetrics.forEach(metric => {
                    const metricKey = metric.key;
                    const metricValue = metrics[metricKey];

                    if (metricValue !== undefined) {
                        console.log(`${metric.display}: ${metricValue}`);
                        updateHealthBar(`${metricKey}_bar`, metricValue, true);
                    } else {
                        console.warn(`Metric ${metricKey} not found in response`);
                    }
                });
            } else {
                // Fallback to hardcoded metrics if currentModeMetrics not loaded
                console.warn('currentModeMetrics not loaded, using fallback');
                if (metrics.staff_retention !== undefined) updateHealthBar('staff_retention_bar', metrics.staff_retention, true);
                if (metrics.partner_growth !== undefined) updateHealthBar('partner_growth_bar', metrics.partner_growth, true);
                if (metrics.partner_retention !== undefined) updateHealthBar('partner_retention_bar', metrics.partner_retention, true);
                if (metrics.tech_debt !== undefined) updateHealthBar('tech_debt_bar', metrics.tech_debt, true);
                if (metrics.revenue !== undefined) updateHealthBar('revenue_bar', metrics.revenue, true);
                if (metrics.net_votes !== undefined) updateHealthBar('net_votes_bar', metrics.net_votes, true);
            }
        }

        function updateHealthBar(barId, value, positiveMetric) {
            const bar = document.getElementById(barId);
            const clampedValue = Math.min(Math.max(value, 0), 100); // Clamp value between 0 and 100

            console.log(`Updating health bar ${barId} to ${clampedValue}%`);

            bar.style.width = clampedValue + '%';

            if (positiveMetric) {
                if (clampedValue >= 67) {
                    bar.style.backgroundColor = 'green';
                } else if (clampedValue >= 34) {
                    bar.style.backgroundColor = 'yellow';
                } else {
                    bar.style.backgroundColor = 'red';
                }
            } else {
                if (clampedValue >= 67) {
                    bar.style.backgroundColor = 'red';
                } else if (clampedValue >= 34) {
                    bar.style.backgroundColor = 'yellow';
                } else {
                    bar.style.backgroundColor = 'green';
                }
            }

            console.log(`Health bar ${barId} style:`, bar.style.cssText); // Log the final style applied to the bar
        }

        async function endGame() {
            const turnsSurvived = parseInt(document.getElementById('turns_survived')?.innerText || 0);
            // Get difficulty from the dropdown selector
            const difficultySelector = document.getElementById('difficulty_selector_settings') || document.getElementById('difficulty_selector_overlay');
            const difficulty = difficultySelector ? difficultySelector.value : 'Normal';
            const wonGame = (gameState === "win");

            // Dynamically collect all metric values based on current mode
            const metricsData = {};
            currentModeMetrics.forEach(metric => {
                const bar = document.getElementById(`${metric.key}_bar`);
                if (bar) {
                    metricsData[metric.key] = parseInt(bar.style.width) || 0;
                }
            });

            console.log("Ending game with the following data:", {
                turns_survived: turnsSurvived,
                difficulty: difficulty,
                won: wonGame,
                ...metricsData
            });

            const response = await fetchWithCSRF('/end_game', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    turns_survived: turnsSurvived,
                    difficulty: difficulty,
                    won: wonGame,
                    ...metricsData
                })
            });

            if (response.ok) {
                const data = await response.json();
                console.log("Game ended:", data);
                showFinalScore(data.scores);
            } else {
                console.error("Failed to end game");
            }

            document.getElementById('start_button').innerText = 'Restart Game';
            document.getElementById('restart_button_bottom').innerText = 'Restart Game';
            document.getElementById('start_button').style.display = 'inline-block';
            document.getElementById('yes_button').classList.add('hidden');
            document.getElementById('no_button').classList.add('hidden');
            document.getElementById('next_button_scenario').classList.add('hidden');
            document.getElementById('next_button_messages').classList.add('hidden');

            if (gameState === "win") {
                document.getElementById('win_gif').classList.remove('hidden');
                document.getElementById('failure_image').classList.add('hidden');
            } else if (gameState === "failure") {
                document.getElementById('win_gif').classList.add('hidden');
                document.getElementById('failure_image').classList.remove('hidden');
            }
        }


        function displayStatusMessage(message, scores) {
            console.log(`Displaying status message: ${message}`);
            if (!message) {
                message = "An unknown error occurred.";
            }

            const messagesDiv = document.getElementById('messages');
            messagesDiv.innerHTML += `<p>${message}</p>`;
            document.getElementById('messages').style.display = 'block';
            document.getElementById('scenario').style.display = 'none';

            if (message.includes("Failure")) {
                gameState = "failure";
                document.getElementById('next_button_messages').classList.add('hidden');
                document.getElementById('next_button_scenario').classList.add('hidden');
                document.getElementById('failure_image').classList.remove('hidden');
            } else if (message.startsWith("Congratulations")) {
                if (message.includes("survived")) {
                    gameState = "win";
                    document.getElementById('win_gif').classList.remove('hidden');
                    document.getElementById('failure_image').classList.add('hidden');
                } else if (message.includes("thriving")) {
                    gameState = "thriving";
                }
            } else {
                document.getElementById('next_button_messages').innerText = 'Next';
                document.getElementById('next_button_messages').classList.remove('hidden');
            }

            document.getElementById('yes_button').classList.add('hidden');
            document.getElementById('no_button').classList.add('hidden');
            turnIncremented = false; // Reset for the next turn

            if ((gameState === "win" || gameState === "failure") && scores) {
                showFinalScore(scores);
            }
        }

        function showFinalScore(scores) {
            console.log("Displaying final score", scores);

            if (!scores || typeof scores.overall_score === 'undefined') {
                console.error("Scores object is invalid or missing necessary properties.", scores);
                return;
            }

            const messagesDiv = document.getElementById('messages');

            // Create final score element
            const finalScoreElement = document.createElement('p');
            finalScoreElement.className = 'px-4 mt-4 font-bold';
            finalScoreElement.id = 'finalScore';
            finalScoreElement.innerText = `Final Score: ${scores.overall_score.toFixed(0)}%`;
            finalScoreElement.classList.remove('hidden'); // Ensure it's visible
            messagesDiv.appendChild(finalScoreElement);

            // Create and show the score details button inside the messages div
            const scoreDetailsButton = document.createElement('button');
            scoreDetailsButton.className = 'inactive py-1 px-4 my-4 mx-4';
            scoreDetailsButton.id = 'scoreDetailsButton';
            scoreDetailsButton.innerText = 'Score Details';
            scoreDetailsButton.onclick = showScoreDetails; // Link to the showScoreDetails function
            messagesDiv.appendChild(scoreDetailsButton);

            // Create and show the restart game button inside the messages div
            const restartGameButton = document.createElement('button');
            restartGameButton.className = 'button py-1 px-4 my-4 mx-4';
            restartGameButton.id = 'restartGameButton';
            restartGameButton.innerText = 'Restart Game';
            restartGameButton.onclick = startGame; // Link to the startGame function
            messagesDiv.appendChild(restartGameButton);

            // Prepare score breakdown for the score details modal
            const scoreBreakdown = `
                Turns: ${scores.turns_score.toFixed(0)}% (${scores.turns_survived}/25 turns)
                <br>Win Bonus: ${scores.win_bonus.toFixed(0)}% (${scores.won_game ? 'Won' : 'Lost'})
                <br>Difficulty: ${scores.difficulty_score}% (${scores.difficulty})
                <br>Points: ${scores.points_score.toFixed(0)}% (${scores.total_points}/400)
                <br><br><strong>Final Score: ${scores.overall_score.toFixed(0)}%</strong>
            `;
            const scoreBreakdownElement = document.getElementById('scoreBreakdown');
            scoreBreakdownElement.innerHTML = scoreBreakdown;
        }

        function showScoreDetails() {
            const scoreDetailsModal = document.getElementById('scoreDetailsModal');
            const settingsModal = document.getElementById('settingsModal');
            if (scoreDetailsModal) {
                scoreDetailsModal.classList.remove('hidden');
                scoreDetailsModal.style.display = 'flex'; // Ensures it displays as a flex container
                console.log('Score details modal displayed');

                // Also trigger the settings modal to open
                if (settingsModal) {
                    settingsModal.classList.remove('hidden');
                    settingsModal.style.display = 'flex'; // Ensures it displays as a flex container
                    console.log('Settings modal displayed');
                } else {
                    console.error('Settings modal not found');
                }
            } else {
                console.error('Score details modal not found');
            }
        }

        function dismissScoreDetails() {
            const scoreDetailsModal = document.getElementById('scoreDetailsModal');
            const settingsModal = document.getElementById('settingsModal');
            if (scoreDetailsModal) {
                scoreDetailsModal.classList.add('hidden');
                scoreDetailsModal.style.display = 'none'; // Ensure it is hidden
                console.log('Score details modal hidden');

                if (settingsModal) {
                    settingsModal.classList.add('hidden');
                    settingsModal.style.display = 'none'; // Ensure it is hidden
                    console.log('Settings modal hidden');
                }
            } else {
                console.error('Score details modal not found');
            }
        }

        function getElementVisibility(element) {
            if (!element) return 'Element not found';
            const style = getComputedStyle(element);
            const rect = element.getBoundingClientRect();
            return {
                display: style.display,
                hiddenClass: element.classList.contains('hidden'),
                width: rect.width,
                height: rect.height,
                visibility: style.visibility,
                opacity: style.opacity
            };
        }

        document.addEventListener('keydown', function(event) {
            console.log('Key pressed:', event.key);

            const activeElement = document.activeElement;
            const isInputField = activeElement.tagName === 'INPUT' || activeElement.tagName === 'TEXTAREA';
            const settingsModal = document.getElementById('settingsModal');
            const overlay = document.getElementById('overlay');
            const createScenarioModal = document.getElementById('createScenarioModal');

            console.log('Active element:', activeElement);
            console.log('Is input field:', isInputField);
            console.log('Settings modal display:', settingsModal.style.display);
            console.log('Overlay display:', overlay.style.display);
            console.log('Create scenario modal display:', createScenarioModal.style.display);
            console.log('Create scenario modal contains active element:', createScenarioModal.contains(activeElement));

            if ((event.key === 'Enter' || event.key === ' ') && (!isInputField || (createScenarioModal.style.display !== 'flex' && !createScenarioModal.contains(activeElement)))) {
                if (settingsModal.style.display === 'flex' || overlay.style.display === 'flex' || createScenarioModal.style.display === 'flex') {
                    event.preventDefault();
                    const okButton = settingsModal.querySelector('.ok-button') || overlay.querySelector('.ok-button') || createScenarioModal.querySelector('.ok-button');
                    if (okButton) {
                        okButton.click();
                    }
                } else {
                    event.preventDefault();
                    const nextButtonScenario = document.getElementById('next_button_scenario');
                    const nextButtonMessages = document.getElementById('next_button_messages');
                    if (isVisible(nextButtonScenario)) {
                        nextButtonScenario.click();
                    } else if (isVisible(nextButtonMessages)) {
                        nextButtonMessages.click();
                    }
                }
            } else if (!isInputField) {
                if (event.key === 'r' || event.key === 'g') {
                    document.getElementById('start_button').click();
                } else if (event.key === 'i') {
                    const settingsButton = document.getElementById('settings_button');
                    if (settingsButton) {
                        settingsButton.click();
                    }
                } else if (event.key.toLowerCase() === 'y') {
                    const yesButton = document.getElementById('yes_button');
                    if (isVisible(yesButton)) {
                        yesButton.click();
                    }
                } else if (event.key.toLowerCase() === 'n') {
                    const noButton = document.getElementById('no_button');
                    if (isVisible(noButton)) {
                        noButton.click();
                    }
                }
            }
        });

        function isVisible(element) {
            const style = getComputedStyle(element);
            const rect = element.getBoundingClientRect();
            return style.display !== 'none' && !element.classList.contains('hidden') && rect.width > 0 && rect.height > 0;
        }

        function getElementDetails(element) {
            if (!element) return 'Element not found';
            const style = getComputedStyle(element);
            const rect = element.getBoundingClientRect();
            return {
                display: style.display,
                hiddenClass: element.classList.contains('hidden'),
                width: rect.width,
                height: rect.height,
                visibility: style.visibility,
                opacity: style.opacity
            };
        }


        function isVisible(element) {
            const style = getComputedStyle(element);
            const rect = element.getBoundingClientRect();
            return style.display !== 'none' && !element.classList.contains('hidden') && rect.width > 0 && rect.height > 0;
        }

        function getElementDetails(element) {
            if (!element) return 'Element not found';
            const style = getComputedStyle(element);
            const rect = element.getBoundingClientRect();
            return {
                display: style.display,
                hiddenClass: element.classList.contains('hidden'),
                width: rect.width,
                height: rect.height,
                visibility: style.visibility,
                opacity: style.opacity
            };
        }

        async function dismissOverlay() {
            // Get the currently selected mode and difficulty to ensure they're applied
            const selectedMode = document.getElementById('mode_selector_overlay').value;
            const selectedDifficulty = document.getElementById('difficulty_selector_overlay').value;

            console.log('Dismissing overlay with mode:', selectedMode, 'difficulty:', selectedDifficulty);

            // Ensure mode and difficulty are set (in case onchange didn't fire)
            if (selectedMode) {
                await setMode(selectedMode);
            }
            if (selectedDifficulty) {
                await setDifficulty(selectedDifficulty);
            }

            document.getElementById('overlay').style.display = 'none';
        }

        let isAuthenticated = false;
        let authCheckTime = null;
        const AUTH_CHECK_INTERVAL = 300000; // 5 minutes in milliseconds

        async function checkAuth() {
            const currentTime = new Date().getTime();
            if (!authCheckTime || (currentTime - authCheckTime) > AUTH_CHECK_INTERVAL) {
                const response = await fetchWithCSRF('/check_auth');
                const data = await response.json();
                isAuthenticated = data.authenticated;
                authCheckTime = currentTime;
                if (!isAuthenticated) {
                    document.getElementById('loginModal').style.display = 'flex';
                } else {
                    document.getElementById('loginModal').style.display = 'none';
                }
            }
        }
        // Reset the game on page refresh
        window.onload = async function() {
            checkAuth();
            await loadAvailableModes(); // Load available modes from configuration
            resetGame().then(() => {
                setDifficulty('Normal'); // Set default difficulty on page load
            });
        };

        document.addEventListener('DOMContentLoaded', function() {
            checkAuth();

            // Show settings modal
            document.getElementById('settings_button').addEventListener('click', async function() {
                await fetchUserInfo();
                const settingsModal = document.getElementById('settingsModal');
                if (settingsModal) {
                    settingsModal.classList.remove('hidden');
                    settingsModal.style.display = 'flex'; // Ensure it is displayed as a flex container
                    console.log('Settings modal displayed');
                } else {
                    console.error('Settings modal not found');
                }
            });

            // Handle login form submission
            document.getElementById('loginForm').addEventListener('submit', async function(event) {
                event.preventDefault(); // Prevent form submission
                const formData = new FormData(event.target);
                console.log('Submitting login form...');
                const response = await fetchWithCSRF('/login', {
                    method: 'POST',
                    body: formData
                });
                console.log('Login response:', response);

                if (response.ok) {
                    const data = await response.json();
                    console.log('Login response data:', data);
                    if (data.authenticated) {
                        document.getElementById('loginModal').style.display = 'none';
                        await resetGame();
                        await setDifficulty('Normal');
                        // Load modes first to get default mode, then set it
                        if (!defaultMode) {
                            await loadAvailableModes();
                        } else {
                            await setMode(defaultMode);
                        }
                        document.getElementById('overlay').style.display = 'flex';
                    } else {
                        alert(data.message || 'Invalid email or password');
                    }
                } else {
                    alert('Login error. Please try again.');
                }
            });

            // Set default tab to open
            document.querySelector('.tab-button').click();
        });

        document.addEventListener('DOMContentLoaded', async function() {
            // Load available modes first to get the default mode from server
            await loadAvailableModes();

            // Set default difficulty
            await setDifficulty('Normal');

            // Update the displayed current difficulty
            document.getElementById('current_difficulty').innerText = 'Normal';
            document.getElementById('current_difficulty_bottom').innerText = 'Normal';

            // Mode will be set by loadAvailableModes() which already updates the UI
        });


       // autofocus on email field 
        document.addEventListener('DOMContentLoaded', function() {
            const loginModal = document.getElementById('loginModal');
            if (loginModal.style.display !== 'none') {
                document.getElementById('email').focus();
            }
        });

        // change state of login button when text is present
        function checkForm() {
            var email = document.getElementById('email').value;
            var password = document.getElementById('password').value;
            var loginButton = document.getElementById('loginButton');

            if (email && password) {
                loginButton.classList.remove('inactive');
                loginButton.classList.add('button');
            } else {
                loginButton.classList.remove('button');
                loginButton.classList.add('inactive');
            }
        }

        // Toggle more/less instructions in the Instructions tab
        function toggleMoreInstructions() {
            const moreInstructions = document.getElementById('more-instructions');
            const toggleButton = document.getElementById('toggle-more-instructions');

            if (moreInstructions.style.display === 'none') {
                moreInstructions.style.display = 'inline';
                toggleButton.textContent = 'Less';
            } else {
                moreInstructions.style.display = 'none';
                toggleButton.textContent = 'More';
            }
        }

        // Show instructions - opens settings modal and switches to Instructions tab
        async function showInstructions() {
            // First, open the settings modal
            await fetchUserInfo();
            const settingsModal = document.getElementById('settingsModal');
            if (settingsModal) {
                settingsModal.classList.remove('hidden');
                settingsModal.style.display = 'flex';
            }

            // Then, programmatically click the Instructions tab button
            const instructionsTabButton = document.querySelector('button.tab-button[onclick*="Instructions"]');
            if (instructionsTabButton) {
                instructionsTabButton.click();
            }
        }
