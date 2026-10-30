import functions as func
import financial_type as fin
import features as fea

# 1. Financial Background Input
def manual_input():

    goals = []

    print("==================Manual Input==================")
    print('')

    # 1.1.1. Asset
    assets = []
    print('---------------------Asset---------------------')

    # asks for regular assets
    cash = input('Total cash or cash equivalent amount: $')
    cash = func.check_float(cash, 0)
    liquid_investment = input('total liquid investment: $')
    liquid_investment = func.check_float(liquid_investment, 0)
    illiquid_investment = input('Total illiquid investment: $')
    illiquid_investment = func.check_float(illiquid_investment, 0)
    inv_return = input('Average annual return of investment (%): ')
    inv_return = func.check_float(inv_return, -100, 100)

    assets.append(fin.Assets('Cash', cash, 1, 0))
    assets.append(fin.Assets('Liquid Investment', liquid_investment, 2, inv_return))
    assets.append(fin.Assets('Illiquid Investment', illiquid_investment, 5, inv_return))


    # ask for extra assets
    while True:
        print('')
        other = input('Do you have other assets (Y/N)? ').strip().upper()
        if other == 'Y' or other == 'YES':
            name = func.check_name('Asset type: ')
            amount = input('Total amount: $')
            amount = func.check_float(amount, 0)
            
            # ask and check liquidity
            liquidity = input('Liquidity [highest: 1 - lowest: 5]: ')
            liquidity = func.check_int(liquidity, 1, 5)    
    
            exp_return = input('Annual return rate (%): ')
            exp_return = func.check_float(exp_return, -100, 100)
            
            assets.append(fin.Assets(name, amount, liquidity, exp_return))
            print(f'{name} is added!')
            continue
        
        elif other == 'N' or other == 'NO':
            print('')
            break
        
        else:
            print('Invalid input.')
            continue

    # 1.1.2. Liability
    print('--------------------Liability--------------------')
    liabilities = []

    # allow user to input loans that they have
    num = input('How many loans/ mortgages do you have? ')
    num = func.check_int(num)
    print('')

    for i in range(num):

        # ask the info of each loan
        print(f'Liability {i+1}')
        name = func.check_name(f'Liability name (Default: Loan {i + 1}): ', default=f'Loan {i + 1}')
        amount = input('Remaining principal amount: $')
        amount = func.check_float(amount, 0)
        interest = input('Annual interest rate (%): ')
        interest = func.check_float(interest, 0, 100)
        repayment = input('Monthly repayment amount: $')
        repayment = func.check_float(repayment, 0)

        liabilities.append(fin.Liabilities(name, amount, interest, repayment))
        print(f'{name} is added!')
        print('')

    # 1.1.3. Income
    print('--------------------Income--------------------')
    incomes = []

    # ask for regular incomes
    incomes.append(fin.Incomes(*func.income_input('Salary')))

    # ask for extra incomes
    while True:
        other = input('Do you have other source of incomes (Y/N)? ').strip().upper()
        if other == 'Y' or other == 'YES':
            name = func.check_name('Income type: ')
            incomes.append(fin.Incomes(*func.income_input(name)))
        elif other == 'N' or other == 'NO':
            print('')
            break
        else:
            print('Invalid input.')
            print('')
            continue

    # 1.1.4. Expense
    print('--------------------Expense--------------------')
    expenses = []

    # ask for regular expenses
    expenses.append(fin.Expenses(*func.expense_input('Food')))
    expenses.append(fin.Expenses(*func.expense_input('Transportation')))
    expenses.append(fin.Expenses(*func.expense_input('Rent')))
    expenses.append(fin.Expenses(*func.expense_input('Clothing')))

    # ask for extra expenses
    while True:
        more = input('Do you have other expenses (Y/N)? ').strip().upper()
        
        if more == 'Y' or more == 'YES':
            name = func.check_name('Expense category: ')
            expenses.append(fin.Expenses(*func.expense_input(name)))
        elif more == 'N' or more == 'NO':
            print('Finished adding expenses!')
            break
        else:
            print('Invalid input.')
            print('')

    print('All financial information logged!')
    print('')

    return assets, liabilities, incomes, expenses, goals

# 1.2. File Financial Background Input
# elif upload == 'file':
def file_input():
    filename = input(
        'Filename [default: finance.txt]: '
    ).strip()

    if not filename:
        filename = 'finance.txt'

    try:
        (
            assets,
            liabilities,
            incomes,
            expenses,
            goals
        ) = fea.load_financial_data(filename)

    except (OSError, ValueError) as error:
        print(f'Unable to load financial information: {error}')
        raise SystemExit

    print('Financial information loaded successfully.')
    print('')

    return assets, liabilities, incomes, expenses, goals

# 2. Application functions
def app_function(assets, liabilities, incomes, expenses, goals):
    while True:
        print(
            'Please input the number of the function to execute.\n'
            '1: View Financial Information\n'
            '2: Budget Planning\n'
            '3: Financial Simulator\n'
            '4: Opportunity Cost Visualiser\n'
            '5: Export Data\n'
            '6: Exit\n'
        )

        # check valid function input
        mode = input('Function: ')
        mode = func.check_int(mode, 1, 6)

        # execute function 1
        if mode == 1:
            
            # choose which data to view
            section = input(f'Section to view [All | Assets | Liabilities | Incomes | Expenses | Goals]: ').strip().lower()
            print('')

            # print corresponding data
            if section == 'all':
                print(fin.Assets.print_table(assets))
                print(fin.Liabilities.print_table(liabilities))
                print(fin.Incomes.print_table(incomes))
                print(fin.Expenses.print_table(expenses))

                
                print('')
                print('Goals:')
                if not goals:
                    print('No active goals.')
                else:
                    for goal in goals:
                        if goal['type'] == 'long':
                            print(f"- {goal['name']}: ${goal['amount']:,.2f} per month")
                        else:
                            print(f"- {goal['name']}: ${goal['saved']:,.2f} saved of ${goal['amount']:,.2f}, deadline {goal['deadline']}")

                print('')
            elif section == 'assets':
                print(fin.Assets.print_table(assets))
                print('')
            elif section == 'liabilities':
                print(fin.Liabilities.print_table(liabilities))
                print('')
            elif section == 'incomes':
                print(fin.Incomes.print_table(incomes))  
                print('')      
            elif section == 'expenses':
                print(fin.Expenses.print_table(expenses)) 
                print('')
            elif section == 'goals':
                print('Goals:')
                if not goals:
                    print('No active goals.')
                else:
                    for goal in goals:
                        if goal['type'] == 'long':
                            print(f"[Long-term] {goal['name']}: ${goal['amount']:,.2f} per month")
                        else:
                            print(f"[Short-term] {goal['name']}: ${goal['saved']:,.2f} saved of ${goal['amount']:,.2f}, deadline {goal['deadline']}")
                print('')
            else:
                print('Invalid Input.')  
                print('')

        # execute function 2
        elif mode == 2:
            fea.budget_planning(
                assets,
                liabilities,
                incomes,
                expenses,
                goals
            )
        
        # execute function 3
        elif mode == 3:
            fea.financial_simulator(
                assets,
                liabilities,
                incomes,
                expenses,
                goals
            )

        # execute function 4
        elif mode == 4:
            fea.opportunity_cost_visualiser(
                assets,
                liabilities,
                incomes,
                expenses,
                goals
            )
        
        # execute function 5
        elif mode == 5:
            fea.export_financial_data(
                'finance.txt',
                assets,
                liabilities,
                incomes,
                expenses,
                goals
            )

        # execute function 6
        elif mode == 6:
            save = fea.yes_no('Export your data before exiting (Y/N)? ')

            if save:
                fea.export_financial_data(
                    'finance.txt',
                    assets,
                    liabilities,
                    incomes,
                    expenses,
                    goals
                )

            print('Program ended.')
            print('')
            break

def main():
    # data input method
    while True:
        upload = input('Financial information by uploading file or manual input [File | Manual]: ').strip().lower()
        print('')

        if upload == 'file' or upload == 'f':
            data = file_input()
            break

        if upload == 'manual' or upload == 'm':
            data = manual_input()
            break

        print("Please enter 'File' or 'Manual'.")
        print('')

    # run the menu functions
    app_function(*data)


if __name__ == '__main__':
    main()





