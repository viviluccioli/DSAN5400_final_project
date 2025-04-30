# NLP Analysis Toolkit

## Overview

This Python project, nlp_analysis, is a modular NLP toolkit for analyzing trends in U.S. news media coverage across ABC, MSNBC, and FOX News from 2015 to 2025. It performs automated topic modeling, sentiment and polarization analysis, and topic half-life decay modeling to better understand how themes emerge, persist, or polarize across networks.

Built using Python 3.12 and poetry, the toolkit is designed with reproducibility and modularity in mind. Each script can be run independently from the command line, and all functionality is fully tested using pytest.

## Key Features

- Topic Modeling using LDA on news headlines and theme metadata
- Half-Life Modeling to estimate the decay/persistence of topics over time
- Sentiment & Semantic Analysis using rule-based (VADER, AFINN) and transformer-based (RoBERTa) methods
- Logging of key script outputs to a logs/ directory
- Fully tested modules with pytest and test coverage configured

## Project Structure

```
.
├── pyproject.toml              # Project configuration
├── poetry.lock                 # Package lock file
├── environment.yml             # Conda environment specification
├── README.md                   
├── logs/                       # Script-generated logs
├── src/
│   └── nlp_analysis/
│       ├── topic_modeling.py       # Topic modeling functions
│       ├── half_life.py            # Half-life modeling of media topics
│       ├── semantic.py             # Sentiment and polarization analysis
│       ├── utils.py                # Shared helper functions
│       └── __init__.py
└── tests/
    ├── topic_modeling_test.py     # Unit tests for topic modeling
    ├── half_life_test.py          # Unit tests for decay modeling
    └── semantic_test.py           # Unit tests for sentiment functions
```

## Setup Instructions

1. Clone the Repository

git clone https://github.com/viviluccioli/DSAN5400_final_project.git
cd nlp_analysis

2. Create the Environment

```bash
git clone https://github.com/<your-repo-url>.git
cd nlp_analysis
```

3. Install Dependencies

poetry install

Running the Analysis Scripts

Each script in src/nlp_analysis is self-contained. Instructions for how to run each one are included at the top of the file.

Examples:

```bash
# Run topic modeling
poetry run python src/nlp_analysis/topic_modeling.py

# Run sentiment & semantic analysis
poetry run python src/nlp_analysis/semantic.py

# Run half-life modeling
poetry run python src/nlp_analysis/half_life.py
```

## Testing

All components are tested using pytest. To run the test suite:

```bash
poetry run pytest tests/ -v
```

You can run tests for individual modules, e.g.:

```bash
poetry run pytest tests/topic_modeling_test.py -v
```

Test coverage is configured through pytest-cov and pyproject.toml.


## Logging


All scripts are instrumented using Python's logging module. Logs are written to the logs/ directory to help trace pipeline execution and results.

## Authors

- Viviana Luccioli (vcl16@georgetown.edu)
- Kristin Lloyd (kml301@georgetown.edu)
- Ria Sonawane (rs2261@georgetown.edu)
- Zixu Hao (zh301@georgetown.edu)


## License

This project is for academic and research purposes under the Georgetown DSAN 5400 course.


## Notes

- Code is formatted with black, ruff, and flake8.
- Data is stored externally or pulled via script; not included in the GitHub repo.
- Diagram of code architecture is included in project documentation.

