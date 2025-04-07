#topic half life modeling 
#measures how long a topic stays alive per political leaning

import pandas as pd
import glob
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from collections import Counter
from scipy.stats import ttest_ind
import matplotlib.dates as mdates

# Set consistent styling for all plots
plt.style.use('seaborn-v0_8-whitegrid')
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['Arial', 'DejaVu Sans', 'Liberation Sans']


# Define sources and their file patterns
sources = {
    'msnbc': glob.glob("../data/msnbc/msnbc*.csv"),
    'abc': glob.glob("../data/abc/abc*.csv"),
    'fox': glob.glob("../data/fox/fox*.csv"),
}

# Read and tag each batch
df_list = []

for source_name, file_list in sources.items():
    for file in file_list:
        df = pd.read_csv(file)
        df['source'] = source_name  # Add source column
        df_list.append(df)

# Combine everything into one DataFrame
combined_df = pd.concat(df_list, ignore_index=True)

# Select relevant columns
columns_of_interest = [
    "parsed_date", "url", "headline_from_url",
    "V2Themes", "V2Locations", "V2Persons",
    "V2Organizations", "V2Tone", "source"
]
combined_df = combined_df[columns_of_interest]

# Convert parsed_date to datetime and ensure it's timezone-naive
combined_df["parsed_date"] = pd.to_datetime(combined_df["parsed_date"], errors="coerce").dt.tz_localize(None)

# Preview structure and missing values
print("DataFrame structure:")
combined_df.info()
print("\nMissing values count:")
print(combined_df.isnull().sum())
print("\nSample data:")
print(combined_df.sample(5))

# Drop missing dates or themes
combined_df = combined_df.dropna(subset=['parsed_date', 'V2Themes'])

# Split semicolon-separated themes and explode
combined_df['V2Themes'] = combined_df['V2Themes'].str.split(';')
combined_df = combined_df.explode('V2Themes')

# clean whitespace
combined_df['V2Themes'] = combined_df['V2Themes'].str.strip()

#count mentions over time
combined_df['V2Tone'] = pd.to_numeric(combined_df['V2Tone'], errors='coerce')

topic_daily = (
    combined_df.groupby(['source','V2Themes', 'parsed_date'])
    .agg(count=('headline_from_url', 'count'), 
         tone=('V2Tone', 'mean'))
    .reset_index()
)

#normalize time (days since first appearance)
# Make sure parsed_date is datetime first
topic_daily['parsed_date'] = pd.to_datetime(topic_daily['parsed_date'])

# Get the first date per topic/source combo
first_dates = topic_daily.groupby(['source','V2Themes'])['parsed_date'].min().reset_index()
first_dates = first_dates.rename(columns={'parsed_date': 'first_date'})

# Merge in the first_date
topic_daily = topic_daily.merge(first_dates, on=['source','V2Themes'])

# Now convert first_date to datetime (if needed)
topic_daily['first_date'] = pd.to_datetime(topic_daily['first_date'])

# Compute days since topic first appeared
topic_daily['days_since'] = (topic_daily['parsed_date'] - topic_daily['first_date']).dt.days

#estimate half-life by exponential decay
from sklearn.linear_model import LinearRegression
import numpy as np

decay_results = []

for (source, topic), group in topic_daily.groupby(['source', 'V2Themes']):
    if len(group) < 5:
        continue

    X = group['days_since'].values.reshape(-1, 1)
    y = np.log1p(group['count'].values)

    model = LinearRegression().fit(X, y)
    lambda_ = -model.coef_[0]
    r2 = model.score(X, y)

    if lambda_ <= 0:
        continue

    half_life = np.log(2) / lambda_

    decay_results.append({
        'source': source,
        'topic': topic,
        'decay_rate': lambda_,
        'half_life_days': half_life,
        'r2': r2,
        'n_obs': len(group),
        'avg_tone': group['tone'].mean(),  # ✅ Use mean tone from group
        'first_date': group['parsed_date'].min()  # ✅ Compute actual first day
    })

half_life_df = pd.DataFrame(decay_results)

# Average half-life per source
print(half_life_df.groupby('source')['half_life_days'].mean().sort_values())

# Plot distributions
import matplotlib.pyplot as plt

half_life_df.boxplot(column='half_life_days', by='source', grid=False)
plt.title("Topic Half-Life by Source")
plt.suptitle('')
plt.ylabel("Half-life (days)")
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()

#topics with shortest or longest half-life
# Longest-lived topics
half_life_df.sort_values(by='half_life_days', ascending=False).head(10)

# Shortest-lived topics
half_life_df.sort_values(by='half_life_days').head(10)

#topic decay over time
half_life_df['year'] = half_life_df['first_date'].dt.year
half_life_df.groupby(['source', 'year'])['half_life_days'].mean().unstack().T.plot()

#agenda comparison
tax_df = half_life_df[half_life_df['topic'].str.startswith('TAX')]
sns.boxplot(data=tax_df, x='source', y='half_life_days')
plt.title("Half-Life of 'TAX' Topics by Source")
plt.ylabel("Half-Life (days)")
plt.xlabel("Source")
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()