// Wheel Builder JavaScript

// Chart configuration constants
const CHART_VISUAL_PADDING_PERCENT = 0.2;  // Add 20% visual space above max recommended tension
const CHART_DEFAULT_MAX_KGF = 300;  // Default max kgf when no recommendation available

// Global chart instance
let tensionChartInstance = null;

/**
 * Show confirmation modal and return a Promise that resolves to true/false
 * @param {string} message - The confirmation message to display
 * @returns {Promise<boolean>} - Resolves to true if confirmed, false if cancelled
 */
function showConfirmModal(message) {
    return new Promise((resolve) => {
        const modalElement = document.getElementById('confirmModal');
        const messageElement = document.getElementById('confirmModalMessage');
        const confirmBtn = document.getElementById('confirmActionBtn');
        const cancelBtn = document.getElementById('confirmCancelBtn');

        // Set the message
        messageElement.textContent = message;

        // Create modal instance
        const modal = new bootstrap.Modal(modalElement);

        // Remove any existing event listeners by cloning buttons
        const newConfirmBtn = confirmBtn.cloneNode(true);
        const newCancelBtn = cancelBtn.cloneNode(true);
        confirmBtn.parentNode.replaceChild(newConfirmBtn, confirmBtn);
        cancelBtn.parentNode.replaceChild(newCancelBtn, cancelBtn);

        // Add new event listeners
        newConfirmBtn.addEventListener('click', () => {
            modal.hide();
            resolve(true);
        });

        newCancelBtn.addEventListener('click', () => {
            modal.hide();
            resolve(false);
        });

        // Handle modal close (X button or backdrop)
        const handleClose = () => {
            resolve(false);
            modalElement.removeEventListener('hidden.bs.modal', handleClose);
        };
        modalElement.addEventListener('hidden.bs.modal', handleClose);

        // Show the modal
        modal.show();
    });
}

/**
 * Initialize tension radar chart
 */
function initTensionChart(leftReadings, rightReadings, leftLabels, rightLabels, recommendedMin, recommendedMax) {
    const ctx = document.getElementById('tensionChart');
    if (!ctx) return;

    // Destroy existing chart if it exists
    if (tensionChartInstance) {
        tensionChartInstance.destroy();
    }

    // Prepare datasets
    const datasets = [];

    // Get label count for array sizing
    const labelCount = (leftLabels || rightLabels || []).length;

    // Always add left side dataset (will show as empty if all null)
    if (leftReadings) {
        datasets.push({
            label: 'Left Side',
            data: leftReadings,
            backgroundColor: 'rgba(54, 162, 235, 0.2)',
            borderColor: 'rgba(54, 162, 235, 1)',
            borderWidth: 2,
            pointBackgroundColor: 'rgba(54, 162, 235, 1)',
            pointBorderColor: '#fff',
            pointHoverBackgroundColor: '#fff',
            pointHoverBorderColor: 'rgba(54, 162, 235, 1)'
        });
    }

    // Always add right side dataset (will show as empty if all null)
    if (rightReadings) {
        datasets.push({
            label: 'Right Side',
            data: rightReadings,
            backgroundColor: 'rgba(153, 102, 255, 0.2)',
            borderColor: 'rgba(153, 102, 255, 1)',
            borderWidth: 2,
            pointBackgroundColor: 'rgba(153, 102, 255, 1)',
            pointBorderColor: '#fff',
            pointHoverBackgroundColor: '#fff',
            pointHoverBorderColor: 'rgba(153, 102, 255, 1)'
        });
    }

    // Always add recommended max reference line if available
    if (recommendedMax && labelCount > 0) {
        const maxData = new Array(labelCount).fill(recommendedMax);
        datasets.push({
            label: 'Max Recommended',
            data: maxData,
            backgroundColor: 'rgba(220, 53, 69, 0.1)',
            borderColor: 'rgba(220, 53, 69, 0.5)',
            borderWidth: 1,
            borderDash: [5, 5],
            pointRadius: 0
        });
    }

    tensionChartInstance = new Chart(ctx, {
        type: 'radar',
        data: {
            labels: leftLabels || rightLabels || [],
            datasets: datasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            scales: {
                r: {
                    beginAtZero: true,
                    min: 0,
                    suggestedMax: recommendedMax ? recommendedMax * (1 + CHART_VISUAL_PADDING_PERCENT) : CHART_DEFAULT_MAX_KGF,
                    ticks: {
                        stepSize: 50
                    }
                }
            },
            plugins: {
                legend: {
                    position: 'top',
                },
                title: {
                    display: true,
                    text: 'Spoke Tension Distribution (kgf)'
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            let label = context.dataset.label || '';
                            if (label) {
                                label += ': ';
                            }
                            label += context.parsed.r.toFixed(1) + ' kgf';
                            return label;
                        }
                    }
                }
            }
        }
    });
}

// Auto-initialize chart if data is available
document.addEventListener('DOMContentLoaded', function() {
    // Chart will be initialized from inline script in template
});

/**
 * Show Bootstrap modal after HTMX loads content
 * This fixes the issue where modals freeze when triggered before content loads
 */
document.body.addEventListener('htmx:afterSwap', function(event) {
    // Check if the swap target is a modal container
    const targetId = event.detail.target.id;

    if (targetId === 'build-modal-container') {
        const modal = new bootstrap.Modal(document.getElementById('build-modal'));
        modal.show();
    } else if (targetId === 'component-modal-container') {
        const modal = new bootstrap.Modal(document.getElementById('component-modal'));
        modal.show();
    } else if (targetId === 'session-modal-container') {
        const modal = new bootstrap.Modal(document.getElementById('session-modal'));
        modal.show();
    }
});
