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
    // State
    let currentYear = 2015;
    let selectedMonth = null;
    let selectedSource = null;
    let yearData = null;
    
    // DOM elements
    const calendarView = document.getElementById('calendarView');
    const calendarTitle = document.getElementById('calendarTitle');
    const prevYearBtn = document.getElementById('prevYear');
    const nextYearBtn = document.getElementById('nextYear');
    const yearSelect = document.getElementById('yearSelect');
    const monthDetailCard = document.getElementById('monthDetailCard');
    const monthDetailTitle = document.getElementById('monthDetailTitle');
    const monthDetailContent = document.getElementById('monthDetailContent');
    
    // Initialize
    yearSelect.value = currentYear;
    loadYearData(currentYear);
    
    // Event listeners
    yearSelect.addEventListener('change', function() {
        currentYear = parseInt(this.value);
        loadYearData(currentYear);
        updateCalendarTitle();
    });
    
    prevYearBtn.addEventListener('click', function() {
        if (currentYear > 2015) {
            currentYear--;
            yearSelect.value = currentYear;
            loadYearData(currentYear);
            updateCalendarTitle();
        }
    });
    
    nextYearBtn.addEventListener('click', function() {
        if (currentYear < 2025) {
            currentYear++;
            yearSelect.value = currentYear;
            loadYearData(currentYear);
            updateCalendarTitle();
        }
    });
    
    // Functions
    function updateCalendarTitle() {
        calendarTitle.textContent = currentYear;
    }
    
    function loadYearData(year) {
        // In a real implementation, this would load from your JSON files
        // For now, we'll use placeholder data
        fetch(`data/data_${year}.json`)
            .then(response => response.json())
            .then(data => {
                yearData = data[year];
                renderCalendar();
            })
            .catch(error => {
                console.error('Error loading data:', error);
                // Use dummy data for demonstration
                generateDummyData(year);
                renderCalendar();
            });
    }
    
    function generateDummyData(year) {
        yearData = {};
        const months = year === 2025 ? 4 : 12;
        
        for (let month = 1; month <= months; month++) {
            yearData[month] = {
                month: month,
                year: year,
                sources: {
                    fox: {
                        top_topics: ["Immigration", "Economy", "Foreign Policy"],
                        sentiment: ["positive", "negative", "neutral"][Math.floor(Math.random() * 3)],
                        tone: ["objective", "aggressive", "supportive"][Math.floor(Math.random() * 3)]
                    },
                    abc: {
                        top_topics: ["Healthcare", "Economy", "Climate Change"],
                        sentiment: ["positive", "negative", "neutral"][Math.floor(Math.random() * 3)],
                        tone: ["objective", "aggressive", "supportive"][Math.floor(Math.random() * 3)]
                    },
                    msnbc: {
                        top_topics: ["Social Justice", "Healthcare", "Climate Change"],
                        sentiment: ["positive", "negative", "neutral"][Math.floor(Math.random() * 3)],
                        tone: ["objective", "aggressive", "supportive"][Math.floor(Math.random() * 3)]
                    }
                }
            };
            
            // Add events for specific months
            if (year === 2020 && month === 3) {
                yearData[month].events = [
                    {name: "COVID-19 pandemic begins", type: "health_crisis", day: 13}
                ];
            }
            if ((year === 2016 || year === 2020 || year === 2024) && month === 11) {
                yearData[month].events = [
                    {name: "US Presidential Election", type: "election", day: year === 2016 ? 8 : (year === 2020 ? 3 : 5)}
                ];
            }
            if (year === 2020 && month === 6) {
                yearData[month].events = [
                    {name: "Black Lives Matter protests", type: "social_movement", day: 1}
                ];
            }
            if (year === 2024 && month === 5) {
                yearData[month].events = [
                    {name: "Pro-Palestinian campus protests", type: "protest", day: 1}
                ];
            }
        }
    }
    
    function renderCalendar() {
        calendarView.innerHTML = '';
        
        const monthNames = [
            "January", "February", "March", "April", 
            "May", "June", "July", "August",
            "September", "October", "November", "December"
        ];
        
        const calendarGrid = document.createElement('div');
        calendarGrid.className = 'row g-4';
        
        // Create a card for each month
        for (let i = 1; i <= 12; i++) {
            // Skip months in 2025 that don't exist yet
            if (currentYear === 2025 && i > 4) continue;
            
            const monthData = yearData[i];
            const monthCard = document.createElement('div');
            monthCard.className = 'col-md-3';
            
            // Add special classes for events
            let cardClasses = 'card h-100';
            let monthHasEvent = false;
            
            if (monthData && monthData.events) {
                monthData.events.forEach(event => {
                    if (event.type === 'election') {
                        cardClasses += ' border-danger';
                        monthHasEvent = true;
                    } else if (event.type === 'health_crisis') {
                        cardClasses += ' border-warning';
                        monthHasEvent = true;
                    } else if (event.type === 'social_movement' || event.type === 'protest') {
                        cardClasses += ' border-info';
                        monthHasEvent = true;
                    }
                });
            }
            
            // Create the month card
            monthCard.innerHTML = `
                <div class="${cardClasses}" data-month="${i}">
                    <div class="card-header">
                        ${monthNames[i-1]}
                        ${monthHasEvent ? '<span class="badge bg-primary ms-2">!</span>' : ''}
                    </div>
                    <div class="card-body">
                        <div class="calendar-month-preview">
                            ${getMonthPreview(monthData)}
                        </div>
                    </div>
                </div>
            `;
            
            monthCard.querySelector('.card').addEventListener('click', function() {
                const month = parseInt(this.dataset.month);
                displayMonthDetails(month);
            });
            
            calendarGrid.appendChild(monthCard);
        }
        
        calendarView.appendChild(calendarGrid);
    }
    
    function getMonthPreview(monthData) {
        if (!monthData) return 'No data available';
        
        let preview = '<div class="small text-muted">';
        
        // Show a snippet of the top topics
        const sources = Object.keys(monthData.sources);
        if (sources.length > 0) {
            const firstSource = sources[0];
            const topics = monthData.sources[firstSource].top_topics.slice(0, 2);
            preview += `Top topics: ${topics.join(', ')}...`;
        }
        
        // Show event badges if any
        if (monthData.events) {
            preview += '<div class="mt-2">';
            monthData.events.forEach(event => {
                let badgeClass = 'bg-secondary';
                if (event.type === 'election') badgeClass = 'bg-danger';
                if (event.type === 'health_crisis') badgeClass = 'bg-warning';
                if (event.type === 'social_movement' || event.type === 'protest') badgeClass = 'bg-info';
                
                preview += `<span class="badge ${badgeClass} me-1">${event.name}</span>`;
            });
            preview += '</div>';
        }
        
        preview += '</div>';
        return preview;
    }
    
    function displayMonthDetails(month) {
        selectedMonth = month;
        const monthData = yearData[month];
        
        if (!monthData) {
            alert('No data available for this month');
            return;
        }
        
        const monthNames = [
            "January", "February", "March", "April", 
            "May", "June", "July", "August",
            "September", "October", "November", "December"
        ];
        
        monthDetailTitle.textContent = `${monthNames[month-1]} ${currentYear}`;
        monthDetailCard.style.display = 'block';
        
        // Create the detail content
        let detailHtml = `
            <div class="row">
                <div class="col-12 mb-3">
                    <div class="d-flex justify-content-between">
                        <h5>Media Coverage Comparison</h5>
                        <button class="btn btn-sm btn-outline-secondary" onclick="document.getElementById('monthDetailCard').style.display='none';">Close</button>
                    </div>
                </div>
            </div>
            
            <div class="row">
        `;
        
        // Add source comparisons
        Object.entries(monthData.sources).forEach(([source, data]) => {
            let sourceTitle = source.toUpperCase();
            if (source === 'fox') sourceTitle += ' (Right-leaning)';
            if (source === 'abc') sourceTitle += ' (Neutral)';
            if (source === 'msnbc') sourceTitle += ' (Left-leaning)';
            
            let sentimentClass = 'text-secondary';
            if (data.sentiment === 'positive') sentimentClass = 'text-success';
            if (data.sentiment === 'negative') sentimentClass = 'text-danger';
            
            let toneClass = 'text-secondary';
            if (data.tone === 'aggressive') toneClass = 'text-danger';
            if (data.tone === 'supportive') toneClass = 'text-success';
            
            detailHtml += `
                <div class="col-md-4">
                    <div class="card h-100">
                        <div class="card-header">
                            ${sourceTitle}
                        </div>
                        <div class="card-body">
                            <h6>Top Topics</h6>
                            <ol>
                                ${data.top_topics.map(topic => `<li>${topic}</li>`).join('')}
                            </ol>
                            
                            <h6>Sentiment</h6>
                            <p class="${sentimentClass}">${data.sentiment.charAt(0).toUpperCase() + data.sentiment.slice(1)}</p>
                            
                            <h6>Tone</h6>
                            <p class="${toneClass}">${data.tone.charAt(0).toUpperCase() + data.tone.slice(1)}</p>
                        </div>
                    </div>
                </div>
            `;
        });
        
        detailHtml += `</div>`;
        
        // Add events section if any
        if (monthData.events && monthData.events.length > 0) {
            detailHtml += `
                <div class="row mt-4">
                    <div class="col-12">
                        <h5>Major Events</h5>
                        <ul class="list-group">
                            ${monthData.events.map(event => 
                                `<li class="list-group-item">
                                    ${event.name} (Day ${event.day})
                                </li>`
                            ).join('')}
                        </ul>
                    </div>
                </div>
            `;
        }
        
        monthDetailContent.innerHTML = detailHtml;
    }
});

