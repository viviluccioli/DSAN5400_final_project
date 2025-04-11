// Add this function at the beginning of your script
function loadYearData(year) {
    // Try to fetch the real data file
    fetch(`data/data_${year}.json`)
        .then(response => {
            if (!response.ok) {
                throw new Error('Data not found');
            }
            return response.json();
        })
        .then(data => {
            yearData = data[year];
            renderCalendar();
        })
        .catch(error => {
            console.warn('Using placeholder data:', error);
            // Only use placeholder if real data isn't available
            generateDummyData(year);
            renderCalendar();
        });
}


document.addEventListener('DOMContentLoaded', function() {
    // Create all year sections
    createYearSections();
    
    // Highlight the current year in navigation
    highlightCurrentYearInNav();
    
    // Set up scroll monitoring to update nav highlighting
    setupScrollMonitoring();
});

function createYearSections() {
    const container = document.getElementById('yearsContainer');
    
    // Clear existing content
    container.innerHTML = '';
    
    // Create sections for each year
    for (let year = 2015; year <= 2025; year++) {
        const yearSection = document.createElement('div');
        yearSection.id = `year-${year}`;
        yearSection.className = 'year-section mb-5';
        
        // Year heading
        const yearHeading = document.createElement('h2');
        yearHeading.className = 'year-heading mb-4';
        yearHeading.textContent = year;
        yearSection.appendChild(yearHeading);
        
        // Month grid - using Bootstrap grid system
        const monthsGrid = document.createElement('div');
        monthsGrid.className = 'row g-4'; // Bootstrap row with gap
        
        // Generate months for this year
        const maxMonth = (year === 2025) ? 4 : 12; // Only show up to April 2025
        
        for (let month = 1; month <= maxMonth; month++) {
            const monthNames = [
                "January", "February", "March", "April", 
                "May", "June", "July", "August",
                "September", "October", "November", "December"
            ];
            
            // Create a month card
            const monthCard = document.createElement('div');
            monthCard.className = 'col-md-3 col-sm-6'; // Bootstrap column
            
            let cardClass = 'card h-100';
            
            // Add special classes for events
            if ((year === 2016 || year === 2020 || year === 2024) && month === 11) {
                cardClass += ' border-danger'; // Elections
            } else if ((year === 2020 && month >= 3) || (year === 2021 && month <= 6)) {
                cardClass += ' border-warning'; // COVID
            } else if (year === 2020 && month === 6) {
                cardClass += ' border-info'; // BLM
            } else if (year === 2024 && month === 5) {
                cardClass += ' border-info'; // Campus protests
            }
            
            // Create card content
            monthCard.innerHTML = `
                <div class="${cardClass}" data-year="${year}" data-month="${month}">
                    <div class="card-header">
                        ${monthNames[month-1]}
                    </div>
                    <div class="card-body">
                        <p>Top topics: Immigration, Economy...</p>
                        ${addEventBadges(year, month)}
                    </div>
                </div>
            `;
            
            // Add click event to show month details
            monthCard.querySelector('.card').addEventListener('click', function() {
                showMonthDetails(year, month);
            });
            
            monthsGrid.appendChild(monthCard);
        }
        
        yearSection.appendChild(monthsGrid);
        container.appendChild(yearSection);
    }
}

function addEventBadges(year, month) {
    let badges = '';
    
    // Election badges
    if ((year === 2016 || year === 2020 || year === 2024) && month === 11) {
        badges += '<span class="badge bg-danger me-1">Election</span>';
    }
    
    // COVID badges
    if ((year === 2020 && month >= 3) || (year === 2021 && month <= 6)) {
        badges += '<span class="badge bg-warning text-dark me-1">COVID-19</span>';
    }
    
    // BLM badge
    if (year === 2020 && month === 6) {
        badges += '<span class="badge bg-info me-1">BLM</span>';
    }
    
    // Campus protests
    if (year === 2024 && month === 5) {
        badges += '<span class="badge bg-info me-1">Campus Protests</span>';
    }
    
    return badges ? `<div class="mt-2">${badges}</div>` : '';
}

function showMonthDetails(year, month) {
    const monthNames = [
        "January", "February", "March", "April", 
        "May", "June", "July", "August",
        "September", "October", "November", "December"
    ];
    
    const title = document.getElementById('monthDetailTitle');
    const content = document.getElementById('monthDetailContent');
    
    title.textContent = `${monthNames[month-1]} ${year}`;
    
    // Content would be populated from your data
    content.innerHTML = `
        <div class="row mb-4">
            <div class="col-md-4">
                <div class="card h-100">
                    <div class="card-header bg-light">
                        Fox News (Right-leaning)
                    </div>
                    <div class="card-body">
                        <h6>Top Topics</h6>
                        <ol>
                            <li>Immigration</li>
                            <li>Economy</li>
                            <li>National Security</li>
                        </ol>
                        <h6>Sentiment</h6>
                        <p class="text-success">Positive</p>
                        <h6>Tone</h6>
                        <p class="text-danger">Aggressive</p>
                    </div>
                </div>
            </div>
            
            <div class="col-md-4">
                <div class="card h-100">
                    <div class="card-header bg-light">
                        ABC News (Neutral)
                    </div>
                    <div class="card-body">
                        <h6>Top Topics</h6>
                        <ol>
                            <li>Healthcare</li>
                            <li>Economy</li>
                            <li>Education</li>
                        </ol>
                        <h6>Sentiment</h6>
                        <p class="text-secondary">Neutral</p>
                        <h6>Tone</h6>
                        <p class="text-info">Objective</p>
                    </div>
                </div>
            </div>
            
            <div class="col-md-4">
                <div class="card h-100">
                    <div class="card-header bg-light">
                        MSNBC (Left-leaning)
                    </div>
                    <div class="card-body">
                        <h6>Top Topics</h6>
                        <ol>
                            <li>Social Justice</li>
                            <li>Healthcare</li>
                            <li>Climate Change</li>
                        </ol>
                        <h6>Sentiment</h6>
                        <p class="text-danger">Negative</p>
                        <h6>Tone</h6>
                        <p class="text-warning">Critical</p>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="card">
            <div class="card-header bg-light">
                Daily Coverage Calendar
            </div>
            <div class="card-body">
                <div class="calendar-grid">
                    <!-- This would be a mini-calendar that shows day-by-day coverage -->
                    <p class="text-center">Daily coverage calendar would go here</p>
                </div>
            </div>
        </div>
    `;
    
    // Show the modal
    const modal = new bootstrap.Modal(document.getElementById('monthDetailModal'));
    modal.show();
}

function scrollToYear(year) {
    const yearElement = document.getElementById(`year-${year}`);
    if (yearElement) {
        yearElement.scrollIntoView({ behavior: 'smooth' });
    }
}

function highlightCurrentYearInNav() {
    // Get all year buttons
    const yearButtons = document.querySelectorAll('#yearNav button');
    
    // Clear active class from all buttons
    yearButtons.forEach(button => {
        button.classList.remove('active');
        button.classList.remove('btn-primary');
        button.classList.add('btn-outline-primary');
    });
    
    // Determine which year is most visible in the viewport
    const yearSections = document.querySelectorAll('.year-section');
    let mostVisibleYear = null;
    let maxVisibleHeight = 0;
    
    yearSections.forEach(section => {
        const rect = section.getBoundingClientRect();
        const visibleHeight = Math.min(rect.bottom, window.innerHeight) - Math.max(rect.top, 0);
        
        if (visibleHeight > maxVisibleHeight) {
            maxVisibleHeight = visibleHeight;
            mostVisibleYear = section.id.split('-')[1];
        }
    });
    
    // If a year is visible, highlight its button
    if (mostVisibleYear) {
        const activeButton = document.querySelector(`#yearNav button[onclick="scrollToYear(${mostVisibleYear})"]`);
        if (activeButton) {
            activeButton.classList.remove('btn-outline-primary');
            activeButton.classList.add('btn-primary');
            activeButton.classList.add('active');
        }
    }
}

function setupScrollMonitoring() {
    // Update active year button on scroll
    window.addEventListener('scroll', function() {
        highlightCurrentYearInNav();
    });
}