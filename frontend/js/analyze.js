document.addEventListener('DOMContentLoaded', () => {
    // =========================================================
    // 1. INITIAL SETUP
    // =========================================================

    const yearEl = document.getElementById('year');
    if (yearEl) {
        yearEl.textContent = new Date().getFullYear();
    }

    const stocksContainer = document.getElementById('stocks-container');
    const btnAddStock = document.getElementById('btn-add-stock');
    const btnAnalyze = document.getElementById('btn-analyze');
    const btnSample = document.getElementById('btn-sample');
    const totalWeightDisplay = document.getElementById('total-weight-display');
    const validationMessage = document.getElementById('validation-message');
    const portfolioForm = document.getElementById('portfolio-form');
    const statusBanner = document.getElementById('status-banner');
    const resultsSection = document.getElementById('results-section');

    const GAMMA = 0.5;

    let sentimentChart = null;
    let allocationChart = null;

    // =========================================================
    // 2. INITIAL PORTFOLIO
    // =========================================================

    addStockRow('AAPL', 50);
    addStockRow('NVDA', 50);

    updateAllocationTracker();

    btnAddStock.addEventListener('click', () => {
        addStockRow('', 0);
        updateAllocationTracker();
    });

    btnSample.addEventListener('click', () => {
        stocksContainer.innerHTML = '';

        addStockRow('AAPL', 40);
        addStockRow('MSFT', 30);
        addStockRow('GOOGL', 30);

        updateAllocationTracker();
    });

    // =========================================================
    // 3. DYNAMIC STOCK INPUT ROWS
    // =========================================================

    function addStockRow(ticker = '', weight = 0) {
        const row = document.createElement('div');
        row.className = 'stock-row';

        row.innerHTML = `
            <input
                type="text"
                class="input-field ticker-input"
                placeholder="Ticker (e.g. AAPL)"
                value="${ticker}"
                required
                style="text-transform: uppercase;"
            >

            <input
                type="number"
                class="input-field weight-input"
                placeholder="Weight %"
                value="${weight}"
                min="0"
                max="100"
                step="1"
                required
            >

            <button
                type="button"
                class="btn btn-danger btn-remove"
            >
                Remove
            </button>
        `;

        const removeButton = row.querySelector('.btn-remove');
        const tickerInput = row.querySelector('.ticker-input');
        const weightInput = row.querySelector('.weight-input');

        removeButton.addEventListener('click', () => {
            if (stocksContainer.children.length > 1) {
                row.remove();
                updateAllocationTracker();
            }
        });

        tickerInput.addEventListener('input', updateAllocationTracker);
        weightInput.addEventListener('input', updateAllocationTracker);

        stocksContainer.appendChild(row);
    }

    // =========================================================
    // 4. PORTFOLIO WEIGHT VALIDATION
    // =========================================================

    function updateAllocationTracker() {
        const weightInputs = document.querySelectorAll('.weight-input');

        let totalWeight = 0;

        weightInputs.forEach(input => {
            totalWeight += parseFloat(input.value) || 0;
        });

        totalWeightDisplay.textContent =
            `${Number(totalWeight.toFixed(2))}%`;

        const isValid = Math.abs(totalWeight - 100) < 0.01;

        if (isValid) {
            totalWeightDisplay.className = 'alloc-badge alloc-valid';

            validationMessage.style.display = 'none';
            btnAnalyze.disabled = false;
        } else {
            totalWeightDisplay.className = 'alloc-badge alloc-invalid';

            validationMessage.textContent =
                `Total allocation must equal 100% (Current: ${Number(totalWeight.toFixed(2))}%)`;

            validationMessage.style.display = 'inline';
            btnAnalyze.disabled = true;
        }
    }

    // =========================================================
    // 5. PORTFOLIO FORM SUBMISSION
    // =========================================================

    portfolioForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        const rows = document.querySelectorAll('.stock-row');
        const holdings = [];

        rows.forEach(row => {
            const ticker = row
                .querySelector('.ticker-input')
                .value
                .trim()
                .toUpperCase();

            const enteredWeight = parseFloat(
                row.querySelector('.weight-input').value
            );

            if (ticker && Number.isFinite(enteredWeight) && enteredWeight > 0) {
                holdings.push({
                    ticker,
                    weight: enteredWeight / 100
                });
            }
        });

        if (holdings.length === 0) {
            return;
        }

        const tickerSet = new Set(holdings.map(h => h.ticker));

        if (tickerSet.size !== holdings.length) {
            statusBanner.style.display = 'block';
            statusBanner.textContent =
                'Please remove duplicate stock tickers before analyzing.';

            return;
        }

        btnAnalyze.disabled = true;

        btnAnalyze.innerHTML = `
            <div class="spinner"></div>
            Analyzing Portfolio...
        `;

        statusBanner.style.display = 'block';

        statusBanner.innerHTML = `
            <p style="color: var(--text-secondary);">
                Analyzing sentiment across ${holdings.length}
                symbols (Good things take time)...
            </p>
        `;

        resultsSection.style.display = 'none';

        try {
            const promises = holdings.map(item =>
                fetch('/api/analyze', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        ticker: item.ticker
                    })
                }).then(async res => {
                    if (!res.ok) {
                        const errData = await res
                            .json()
                            .catch(() => ({}));

                        throw new Error(
                            errData.detail ||
                            `Failed to analyze ${item.ticker}`
                        );
                    }

                    return res.json();
                })
            );

            const apiResults = await Promise.all(promises);

            renderResults(holdings, apiResults);

            statusBanner.style.display = 'none';

        } catch (error) {
            statusBanner.style.display = 'block';
            statusBanner.textContent = `Error: ${error.message}`;

        } finally {
            btnAnalyze.disabled = false;

            btnAnalyze.innerHTML = `
                <span>Analyze Portfolio</span>
            `;

            updateAllocationTracker();
        }
    });

    // =========================================================
    // 6. RENDER PORTFOLIO RESULTS
    // =========================================================

    function renderResults(holdings, apiResults) {
        let weightedPortfolioScore = 0;

        const tableBody = document.getElementById(
            'ticker-results-body'
        );

        const headlinesContainer = document.getElementById(
            'headlines-container'
        );

        tableBody.innerHTML = '';
        headlinesContainer.innerHTML = '';

        // -----------------------------------------------------
        // STEP A: Extract sentiment scores
        // -----------------------------------------------------

        const sentimentScores = holdings.map((holding, idx) => {
            const score = apiResults[idx]?.ensemble_score;

            return (
                typeof score === 'number' &&
                Number.isFinite(score)
            ) ? score : 0;
        });

        // -----------------------------------------------------
        // STEP B: Calculate sentiment-adjusted allocations
        // -----------------------------------------------------

        const rawAdjustedWeights = holdings.map((holding, idx) => {
            const originalWeight = holding.weight;
            const sentimentScore = sentimentScores[idx];

            const rawWeight =
                originalWeight *
                (1 + GAMMA * sentimentScore);

            return Math.max(rawWeight, 0);
        });

        const totalRawWeight = rawAdjustedWeights.reduce(
            (sum, weight) => sum + weight,
            0
        );

        const adjustedWeights = rawAdjustedWeights.map(weight => {
            return totalRawWeight > 0
                ? weight / totalRawWeight
                : 0;
        });

        // -----------------------------------------------------
        // STEP C: Populate the asset breakdown table
        // -----------------------------------------------------

        holdings.forEach((holding, idx) => {
            const res = apiResults[idx];

            const tickerScore = sentimentScores[idx];

            const originalWeight = holding.weight;
            const adjustedWeight = adjustedWeights[idx];

            const weightedContribution =
                originalWeight * tickerScore;

            weightedPortfolioScore += weightedContribution;

            const models = res.model_average_scores || {};

            const formatScore = val => {
                return (
                    val !== null &&
                    val !== undefined &&
                    Number.isFinite(val)
                ) ? val.toFixed(3) : 'N/A';
            };

            const tr = document.createElement('tr');

            tr.innerHTML = `
                <td><strong>${holding.ticker}</strong></td>

                <td>${(originalWeight * 100).toFixed(1)}%</td>

                <td>${formatScore(models.finbert)}</td>

                <td>${formatScore(models.reyzer)}</td>

                <td>${formatScore(models.vader)}</td>

                <td>${formatScore(models.textblob)}</td>

                <td><strong>${tickerScore.toFixed(3)}</strong></td>

                <td style="color: ${
                    weightedContribution >= 0
                        ? 'var(--sentiment-pos)'
                        : 'var(--sentiment-neg)'
                };">
                    ${weightedContribution >= 0 ? '+' : ''}
                    ${weightedContribution.toFixed(3)}
                </td>
            `;

            tableBody.appendChild(tr);
        });

        // -----------------------------------------------------
        // STEP D: Populate financial headlines
        // -----------------------------------------------------

        holdings.forEach((holding, idx) => {
            const res = apiResults[idx];

            if (res.articles && res.articles.length > 0) {
                res.articles.forEach(art => {
                    const item = document.createElement('div');

                    item.className = 'headline-item';

                    let badgeClass = 'badge-neutral';

                    if (art.ensemble_sentiment === 'positive') {
                        badgeClass = 'badge-positive';
                    }

                    if (art.ensemble_sentiment === 'negative') {
                        badgeClass = 'badge-negative';
                    }

                    const tickerLabel = document.createElement('span');

                    tickerLabel.style.fontSize = '0.75rem';
                    tickerLabel.style.color = 'var(--accent-indigo)';
                    tickerLabel.style.fontWeight = '600';
                    tickerLabel.textContent = `[${holding.ticker}]`;

                    const headlineText = document.createElement('span');

                    headlineText.className = 'headline-text';
                    headlineText.textContent =
                        art.title || 'Untitled headline';

                    const headlineInfo = document.createElement('div');

                    headlineInfo.appendChild(tickerLabel);
                    headlineInfo.appendChild(headlineText);

                    const sentimentBadge = document.createElement('span');

                    sentimentBadge.className =
                        `score-badge ${badgeClass}`;

                    sentimentBadge.style.fontSize = '0.75rem';
                    sentimentBadge.style.padding = '0.2rem 0.6rem';

                    sentimentBadge.textContent =
                        art.ensemble_sentiment || 'neutral';

                    item.appendChild(headlineInfo);
                    item.appendChild(sentimentBadge);

                    headlinesContainer.appendChild(item);
                });
            }
        });

        // -----------------------------------------------------
        // STEP E: Update portfolio conviction card
        // -----------------------------------------------------

        const scoreDisplay = document.getElementById(
            'portfolio-score-num'
        );

        const badgeDisplay = document.getElementById(
            'portfolio-sentiment-badge'
        );

        scoreDisplay.textContent =
            (weightedPortfolioScore >= 0 ? '+' : '') +
            weightedPortfolioScore.toFixed(3);

        if (weightedPortfolioScore > 0.05) {
            badgeDisplay.textContent = 'Positive Conviction';
            badgeDisplay.className =
                'score-badge badge-positive';

        } else if (weightedPortfolioScore < -0.05) {
            badgeDisplay.textContent = 'Negative Conviction';
            badgeDisplay.className =
                'score-badge badge-negative';

        } else {
            badgeDisplay.textContent = 'Neutral / Balanced';
            badgeDisplay.className =
                'score-badge badge-neutral';
        }

        // -----------------------------------------------------
        // STEP F: Render sentiment chart
        // -----------------------------------------------------

        const sentimentCanvas = document.getElementById(
            'sentimentChart'
        );

        if (sentimentCanvas && typeof Chart !== 'undefined') {
            if (sentimentChart) {
                sentimentChart.destroy();
            }

            sentimentCanvas.parentElement.style.height = '300px';
            sentimentCanvas.parentElement.style.position = 'relative';

            sentimentChart = new Chart(sentimentCanvas, {
                type: 'bar',

                data: {
                    labels: holdings.map(h => h.ticker),

                    datasets: [{
                        label: 'Ensemble Sentiment',

                        data: sentimentScores,

                        backgroundColor: sentimentScores.map(score =>
                            score >= 0
                                ? 'rgba(52, 211, 153, 0.75)'
                                : 'rgba(248, 113, 113, 0.75)'
                        ),

                        borderColor: sentimentScores.map(score =>
                            score >= 0
                                ? '#34d399'
                                : '#f87171'
                        ),

                        borderWidth: 1,
                        borderRadius: 6
                    }]
                },

                options: {
                    responsive: true,
                    maintainAspectRatio: false,

                    plugins: {
                        legend: {
                            display: false
                        },

                        tooltip: {
                            callbacks: {
                                label: context =>
                                    `Sentiment: ${context.parsed.y.toFixed(3)}`
                            }
                        }
                    },

                    scales: {
                        y: {
                            min: -1,
                            max: 1,

                            title: {
                                display: true,
                                text: 'Sentiment Score',
                                color: '#a1a1aa'
                            },

                            ticks: {
                                color: '#a1a1aa'
                            },

                            grid: {
                                color: 'rgba(255,255,255,0.08)'
                            }
                        },

                        x: {
                            ticks: {
                                color: '#a1a1aa'
                            },

                            grid: {
                                display: false
                            }
                        }
                    }
                }
            });
        }

        // -----------------------------------------------------
        // STEP G: Render allocation comparison chart
        // -----------------------------------------------------

        const allocationCanvas = document.getElementById(
            'allocationChart'
        );

        if (allocationCanvas && typeof Chart !== 'undefined') {
            if (allocationChart) {
                allocationChart.destroy();
            }

            allocationCanvas.parentElement.style.height = '300px';
            allocationCanvas.parentElement.style.position = 'relative';

            allocationChart = new Chart(allocationCanvas, {
                type: 'bar',

                data: {
                    labels: holdings.map(h => h.ticker),

                    datasets: [
                        {
                            label: 'Original Allocation (%)',

                            data: holdings.map(h => h.weight * 100),

                            backgroundColor: 'rgba(129, 140, 248, 0.75)',
                            borderColor: '#818cf8',

                            borderWidth: 1,
                            borderRadius: 5
                        },

                        {
                            label: 'Sentiment-Adjusted (%)',

                            data: adjustedWeights.map(w => w * 100),

                            backgroundColor: 'rgba(52, 211, 153, 0.75)',
                            borderColor: '#34d399',

                            borderWidth: 1,
                            borderRadius: 5
                        }
                    ]
                },

                options: {
                    responsive: true,
                    maintainAspectRatio: false,

                    plugins: {
                        legend: {
                            position: 'bottom',

                            labels: {
                                color: '#d4d4d8',
                                padding: 16
                            }
                        },

                        tooltip: {
                            callbacks: {
                                label: context =>
                                    `${context.dataset.label}: ${context.parsed.y.toFixed(2)}%`
                            }
                        }
                    },

                    scales: {
                        y: {
                            beginAtZero: true,
                            max: 100,

                            title: {
                                display: true,
                                text: 'Allocation (%)',
                                color: '#a1a1aa'
                            },

                            ticks: {
                                color: '#a1a1aa',
                                callback: value => `${value}%`
                            },

                            grid: {
                                color: 'rgba(255,255,255,0.08)'
                            }
                        },

                        x: {
                            ticks: {
                                color: '#a1a1aa'
                            },

                            grid: {
                                display: false
                            }
                        }
                    }
                }
            });
        }

        // -----------------------------------------------------
        // STEP H: SENTIMENT VERDICT
        // -----------------------------------------------------

        const positiveList = document.getElementById(
            'verdict-positive-list'
        );

        const negativeList = document.getElementById(
            'verdict-negative-list'
        );

        const neutralList = document.getElementById(
            'verdict-neutral-list'
        );

        const overallBadge = document.getElementById(
            'verdict-overall-badge'
        );

        positiveList.innerHTML = '';
        negativeList.innerHTML = '';
        neutralList.innerHTML = '';

        const positiveStocks = [];
        const negativeStocks = [];
        const neutralStocks = [];
        const unavailableStocks = [];

        // Classify every holding using its actual API score.
        // Negative means strictly below zero.
        holdings.forEach((holding, idx) => {
            const res = apiResults[idx];

            const rawScore = res?.ensemble_score;

            // Do not convert null or missing values into zero.
            if (
                rawScore === null ||
                rawScore === undefined ||
                rawScore === '' ||
                !Number.isFinite(Number(rawScore))
            ) {
                unavailableStocks.push({
                    ticker: holding.ticker,
                    weight: holding.weight * 100
                });

                return;
            }

            const score = Number(rawScore);

            const stock = {
                ticker: holding.ticker,
                score: score,
                weight: holding.weight * 100
            };

            if (score > 0.05) {
                positiveStocks.push(stock);
            } else if (score < 0) {
                // Every negative score goes here.
                negativeStocks.push(stock);
            } else {
                // Scores from 0 through +0.05 are neutral.
                neutralStocks.push(stock);
            }
        });

        // Render each stock inside its appropriate section.
        function renderVerdictStock(stock, container, type) {
            const item = document.createElement('div');
            item.className = 'verdict-stock';

            const ticker = document.createElement('strong');
            ticker.textContent = stock.ticker;

            const details = document.createElement('span');

            details.textContent =
                `Score: ${stock.score >= 0 ? '+' : ''}${stock.score.toFixed(3)} · ` +
                `Current weight: ${stock.weight.toFixed(1)}%`;

            const signal = document.createElement('span');

            signal.className = `verdict-signal ${type}`;

            if (type === 'positive') {
                signal.textContent =
                    'Positive news sentiment — review before considering an increase.';
            } else {
                signal.textContent =
                    'Negative news sentiment — consider reviewing your position or reducing exposure.';
            }

            item.append(ticker, details, signal);

            container.appendChild(item);
        }

        // Positive sentiment section.
        if (positiveStocks.length > 0) {
            positiveStocks.forEach(stock => {
                renderVerdictStock(
                    stock,
                    positiveList,
                    'positive'
                );
            });
        } else {
            positiveList.textContent =
                'No positive sentiment signals.';
        }

        // Negative sentiment section.
        if (negativeStocks.length > 0) {
            negativeStocks.forEach(stock => {
                renderVerdictStock(
                    stock,
                    negativeList,
                    'negative'
                );
            });
        } else {
            negativeList.textContent =
                'No negative sentiment signals.';
        }

        // Neutral sentiment section.
        if (neutralStocks.length > 0) {
            neutralList.textContent =
                'Neutral sentiment: ' +
                neutralStocks.map(stock => stock.ticker).join(', ');
        }

        // Missing score section.
        if (unavailableStocks.length > 0) {
            const unavailableText =
                'Sentiment score unavailable: ' +
                unavailableStocks.map(stock => stock.ticker).join(', ');

            if (neutralList.textContent) {
                neutralList.textContent += ' · ' + unavailableText;
            } else {
                neutralList.textContent = unavailableText;
            }
        }

        // Overall verdict badge.
        if (positiveStocks.length > 0 && negativeStocks.length > 0) {
            overallBadge.textContent = 'Mixed Signals';
            overallBadge.className =
                'score-badge badge-neutral';

        } else if (positiveStocks.length > 0) {
            overallBadge.textContent = 'Positive Signals';
            overallBadge.className =
                'score-badge badge-positive';

        } else if (negativeStocks.length > 0) {
            overallBadge.textContent = 'Negative Signals';
            overallBadge.className =
                'score-badge badge-negative';

        } else {
            overallBadge.textContent = 'Neutral Signals';
            overallBadge.className =
                'score-badge badge-neutral';
        }

        resultsSection.style.display = 'grid';
    }
});