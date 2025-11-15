// Wheel Builder JavaScript

/**
 * Initialize tension radar chart
 */
function initTensionChart(leftReadings, rightReadings, leftLabels, rightLabels, recommendedMin, recommendedMax) {
    const ctx = document.getElementById('tensionChart');
    if (!ctx) return;

    // Prepare datasets
    const datasets = [];

    if (leftReadings && leftReadings.length > 0) {
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

    if (rightReadings && rightReadings.length > 0) {
        datasets.push({
            label: 'Right Side',
            data: rightReadings,
            backgroundColor: 'rgba(255, 99, 132, 0.2)',
            borderColor: 'rgba(255, 99, 132, 1)',
            borderWidth: 2,
            pointBackgroundColor: 'rgba(255, 99, 132, 1)',
            pointBorderColor: '#fff',
            pointHoverBackgroundColor: '#fff',
            pointHoverBorderColor: 'rgba(255, 99, 132, 1)'
        });
    }

    // Add recommended range as reference
    if (recommendedMax) {
        const maxData = new Array(leftReadings?.length || rightReadings?.length || 0).fill(recommendedMax);
        datasets.push({
            label: 'Max Recommended',
            data: maxData,
            backgroundColor: 'rgba(255, 206, 86, 0.1)',
            borderColor: 'rgba(255, 206, 86, 0.5)',
            borderWidth: 1,
            borderDash: [5, 5],
            pointRadius: 0
        });
    }

    new Chart(ctx, {
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
                    suggestedMax: recommendedMax ? recommendedMax * 1.2 : 300,
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
