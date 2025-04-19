// Minimal tone data structure
const toneData = {
    avg_tone: {
        // Add sample data for 2015
        "2015": {
            "1": -2.5,  // January
            "2": -1.8,  // February
            "3": -3.2,  // March
            "4": -2.1,  // April
            "5": -1.5,  // May
            "6": -1.9,  // June
            "7": -2.2,  // July
            "8": -1.7,  // August
            "9": -2.8,  // September
            "10": -3.5, // October
            "11": -4.2, // November
            "12": -3.8  // December
        }
    },
    source_tone: {
        fox: {
            "2015": {
                "1": -1.5,
                "2": -1.2
            }
        },
        abc: {
            "2015": {
                "1": -2.8,
                "2": -2.0
            }
        },
        msnbc: {
            "2015": {
                "1": -3.2,
                "2": -2.4
            }
        }
    },
    metadata: {
        min_tone: -5,
        max_tone: 5
    }
};