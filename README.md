# 💸 Money Debugger

**Money Debugger** is a personal-finance application that helps users track their financial information, create savings goals, plan a budget, and understand the opportunity cost of purchases.

## Features

- Record assets, liabilities, income, and expenses
- Calculate monthly cash flow
- Create short-term and long-term savings goals
- Recommend expense reductions
- Explore financial scenarios without changing saved data
- Compare purchases using opportunity cost
- Import and export financial data

## How to Run

```bash
python main.py
```

## User Guide

When the program starts, choose how to provide your financial information:

- **Manual** — enter new information
- **File** — load previously exported information

Follow the prompts to enter your:

- Assets
- Liabilities
- Income
- Monthly expenses

The main menu provides the following options:

1. **View Financial Information** — review your recorded data  
2. **Budget Planning** — create goals and receive budget suggestions  
3. **Financial Simulator** — explore hypothetical financial changes  
4. **Opportunity Cost Visualiser** — examine the impact of a purchase  
5. **Export Data** — save your information to a file  
6. **Exit** — close the program  

## Important Input Notes

- Enter money as numbers without `$` or commas.
- Enter rates as percentages. For example, enter `5` for 5%.
- Use `Y` or `N` for yes/no questions.
- Priority `1` expenses are reduced before lower-priority expenses.
- Priority `0` expenses are non-reducible.
