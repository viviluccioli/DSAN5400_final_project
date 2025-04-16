// calendar.js with debugging

document.addEventListener('DOMContentLoaded', function() {
    console.log("DOM loaded, starting data loading process...");
    
    // Load topic data first, then create the calendar
    loadTopicData().then(() => {
        console.log("Topic data loading complete, creating calendar sections...");
        // Create all year sections
        createYearSections();
        
        // Highlight the current year in navigation
        highlightCurrentYearInNav();
        
        // Set up scroll monitoring to update nav highlighting
        setupScrollMonitoring();
        
        // Set up year navigation buttons
        setupYearNavigation();
    });
});

// Keep track of loaded topic data
const topicData = {
    fox: {},
    abc: {},
    msnbc: {}
};

// Load topic data from JSON file
async function loadTopicData() {
    try {
        console.log("Starting to load topic data...");
        // Log current URL for debugging
        console.log("Current page URL:", window.location.href);
        
        // Try different possible paths for the JSON file
        const possiblePaths = [
            './data/media_topics.json',
            '../data/media_topics.json',
            '../../data/media_topics.json',
            '../../../data/media_topics.json',
            'data/media_topics.json',
            '/data/media_topics.json',
            '/website/data/media_topics.json'
        ];
        
        let dataLoaded = false;
        
        // Try each path until successful
        for (const path of possiblePaths) {
            try {
                console.log(`Trying to load from ${path}...`);
                const response = await fetch(path);
                console.log(`Fetch response for ${path}:`, response.status, response.statusText);
                
                if (response.ok) {
                    const data = await response.json();
                    console.log("Data loaded successfully:", data);
                    
                    // See if data looks valid
                    if (!data.fox || !data.abc || !data.msnbc) {
                        console.warn("Data loaded but seems invalid (missing source data)");
                        continue;
                    }
                    
                    // Copy the loaded data into our topicData structure
                    Object.assign(topicData.fox, data.fox || {});
                    Object.assign(topicData.abc, data.abc || {});
                    Object.assign(topicData.msnbc, data.msnbc || {});
                    
                    console.log(`Successfully loaded topic data from ${path}`);
                    console.log("Fox data sample:", topicData.fox);
                    dataLoaded = true;
                    break;
                }
            } catch (e) {
                // Continue to next path
                console.warn(`Failed to load from ${path}:`, e.message);
            }
        }
        
        // If data couldn't be loaded from any path, use placeholder data
        if (!dataLoaded) {
            console.warn('Could not load topic data. Using placeholder data instead.');
            generatePlaceholderData();
        }
        
    } catch (error) {
        console.error('Error loading topic data:', error);
        generatePlaceholderData();
    }
}

// Function to generate placeholder data when JSON file can't be loaded
function generatePlaceholderData() {
    console.log("Generating placeholder data...");
    // Create some sample data for visualization testing
    const years = [2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025];
    
    const foxTopics = ['Immigration', 'Economy', 'National Security', 'Crime', 'Foreign Policy', 'Military'];
    const abcTopics = ['Healthcare', 'Economy', 'Education', 'Politics', 'International', 'Science'];
    const msnbcTopics = ['Social Justice', 'Healthcare', 'Climate Change', 'Economy', 'Education', 'Civil Rights'];
    
    // Generate data for each source, year and month
    for (const year of years) {
        topicData.fox[year] = {};
        topicData.abc[year] = {};
        topicData.msnbc[year] = {};
        
        const maxMonth = year === 2025 ? 4 : 12;
        
        for (let month = 1; month <= maxMonth; month++) {
            // Generate Fox topics
            topicData.fox[year][month] = [
                { topic: foxTopics[Math.floor(Math.random() * 3)], rank: 1 },
                { topic: foxTopics[Math.floor(Math.random() * 3) + 3], rank: 2 },
                { topic: 'Other', rank: 3 }
            ];
            
            // Generate ABC topics
            topicData.abc[year][month] = [
                { topic: abcTopics[Math.floor(Math.random() * 3)], rank: 1 },
                { topic: abcTopics[Math.floor(Math.random() * 3) + 3], rank: 2 },
                { topic: 'Other', rank: 3 }
            ];
            
            // Generate MSNBC topics
            topicData.msnbc[year][month] = [
                { topic: msnbcTopics[Math.floor(Math.random() * 3)], rank: 1 },
                { topic: msnbcTopics[Math.floor(Math.random() * 3) + 3], rank: 2 },
                { topic: 'Other', rank: 3 }
            ];
        }
    }
    console.log("Placeholder data generated. Sample:", topicData.fox[2015][1]);
}

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
            
            // Create card content - no topics shown in calendar view as requested
            monthCard.innerHTML = `
                <div class="${cardClass}" data-year="${year}" data-month="${month}">
                    <div class="card-header">
                        ${monthNames[month-1]}
                    </div>
                    <div class="card-body">
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
    console.log("Year sections created successfully");
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

function getTopicsForSource(source, year, month) {
    // Convert to strings to match JSON format from Python
    const yearStr = year.toString();
    const monthStr = month.toString();
    
    // Log what we're looking for to help debug
    console.log(`Looking for topics for ${source}, year: ${yearStr}, month: ${monthStr}`);
    console.log(`Available years for ${source}:`, Object.keys(topicData[source]));
    
    if (topicData[source][yearStr] && topicData[source][yearStr][monthStr]) {
        console.log(`Found topics using string keys: ${topicData[source][yearStr][monthStr].length} topics`);
        return topicData[source][yearStr][monthStr];
    }
    
    // Try numeric keys as well (fallback)
    if (topicData[source][year] && topicData[source][year][month]) {
        console.log(`Found topics using numeric keys: ${topicData[source][year][month].length} topics`);
        return topicData[source][year][month];
    }
    
    console.log(`No topics found for ${source}, year: ${year}, month: ${month}`);
    return [
        { topic: "Topic data unavailable", rank: 1 },
        { topic: "Please check data files", rank: 2 },
        { topic: "Or refresh page", rank: 3 }
    ];
}

function showMonthDetails(year, month) {
    console.log(`Showing details for year ${year}, month ${month}`);
    
    const monthNames = [
        "January", "February", "March", "April", 
        "May", "June", "July", "August",
        "September", "October", "November", "December"
    ];
    
    const title = document.getElementById('monthDetailTitle');
    const content = document.getElementById('monthDetailContent');
    
    title.textContent = `${monthNames[month-1]} ${year}`;
    
    // Get topics for each source
    const foxTopics = getTopicsForSource('fox', year, month);
    const abcTopics = getTopicsForSource('abc', year, month);
    const msnbcTopics = getTopicsForSource('msnbc', year, month);
    
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
                            <li>${foxTopics[0]?.topic || 'No data'}</li>
                            <li>${foxTopics[1]?.topic || 'No data'}</li>
                            <li>${foxTopics[2]?.topic || 'No data'}</li>
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
                            <li>${abcTopics[0]?.topic || 'No data'}</li>
                            <li>${abcTopics[1]?.topic || 'No data'}</li>
                            <li>${abcTopics[2]?.topic || 'No data'}</li>
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
                            <li>${msnbcTopics[0]?.topic || 'No data'}</li>
                            <li>${msnbcTopics[1]?.topic || 'No data'}</li>
                            <li>${msnbcTopics[2]?.topic || 'No data'}</li>
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
                Topic Distribution
            </div>
            <div class="card-body">
                <div id="topicChart" style="height: 300px;">
                    <p class="text-center text-muted">Topic comparison chart would appear here.</p>
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

function setupYearNavigation() {
    // Get the prev/next buttons
    const prevYearButton = document.getElementById('prevYear');
    const nextYearButton = document.getElementById('nextYear');
    const yearSelect = document.getElementById('yearSelect');
    
    if (yearSelect) {
        // Year select dropdown
        yearSelect.addEventListener('change', function() {
            const currentYear = parseInt(this.value);
            scrollToYear(currentYear);
        });
    }
    
    if (prevYearButton && nextYearButton) {
        let currentYear = 2015;
        
        // Previous year button
        prevYearButton.addEventListener('click', function() {
            if (currentYear > 2015) {
                currentYear--;
                scrollToYear(currentYear);
                if (yearSelect) yearSelect.value = currentYear;
            }
        });
        
        // Next year button
        nextYearButton.addEventListener('click', function() {
            if (currentYear < 2025) {
                currentYear++;
                scrollToYear(currentYear);
                if (yearSelect) yearSelect.value = currentYear;
            }
        });
    }
}