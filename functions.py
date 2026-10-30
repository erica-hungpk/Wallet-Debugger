#  check positive number input
def check_int(amount, lower_range = 0, upper_range = 0):
    while True:
        try:
            amount = int(amount)

            # detect negative number
            if amount < 0:
                amount = input('Please enter a positive whole number: ')
                continue
            
            # detect if number is within range
            if upper_range != 0:
                if amount < lower_range or amount > upper_range:
                    amount = input(f'Please enter a number within {lower_range} - {upper_range}: ')
                    continue
            break
        except ValueError:
            amount = input('Please enter a valid number: ')

    return amount

def check_float(amount, lower_range = None, upper_range = None):
    while True:
        try:
            amount = float(amount)
            
            # detect if number is within range
            if upper_range is not None and lower_range is not None:
                if amount < lower_range or amount > upper_range:
                    amount = input(f'Please enter a number within {lower_range} - {upper_range}: ')
                    continue
            elif lower_range is not None and upper_range is None:
                if amount < lower_range:
                    amount = input(f'Please enter a number larger than {lower_range}: ')    
                    continue
            elif lower_range is None and upper_range is not None:
                if amount > upper_range:
                    amount = input(f'Please enter a number lower than {upper_range}: ')    
                    continue
            
            return amount
            
        except ValueError:
            amount = input('Please enter a valid number: ')

# input incomes, return the Incomes class attributes
def income_input(name):
    # general info of income
    amount = input(f'Monthly income on {name}: $')
    amount = check_float(amount, 0)
    
    if name == 'Salary':
        print(f'{name} is added!')
        print('')
        return name, amount, True

    # check recurring status
    while True:  
        recurring = input('Is it a recurring or one-time income (R for recurring,  O for one-time)? ').strip().upper()
        if recurring == 'R' or recurring == 'RECURRING':
            recurring = True
            break
        elif recurring == 'O' or recurring == 'ONE-TIME':
            recurring = False
            break
        else:
            print('Invalid input.')
    
    print(f'{name} is added!')
    print('')
    
    return name, amount, recurring



# input expenses, return the Expenses class attributes
def expense_input(name):
    amount = input(f'Monthly spending on {name}: $')
    amount = check_float(amount, 0)
    
    # check if the amount is reducible
    while True:
        reducible = input('Is the amount reducible (Y/N)? ').strip().upper()
        if reducible == 'Y' or reducible == 'YES':

            # ask for the minimum amount
            # check if it is lower than the average amount
            while True:
                min_amount = input('Monthly minimum spending: $')
                min_amount = check_float(min_amount, 0, amount)
                if min_amount >= amount:
                    print('The minimum amount must be smaller than the average amount.')
                else:
                    break

            # ask for the priority to reduce the expense_input
            rank = input('Priority of reducing expense (highest: 1 - lowest: 5): ')
            rank = check_int(rank, 1, 5)
            
            print(f'{name} is added!')
            print('')
            return name, amount, True, min_amount, rank
        
        elif reducible == 'N' or reducible == 'NO':
            print(f'{name} is added!')
            print('')            
            return name, amount
        
        else:
            print('Invalid input.')

def read_boolean(value):
    if value == 'True':
        return True
    if value == 'False':
        return False

    raise ValueError(f"expected 'True' or 'False', received {value!r}")

def check_name(prompt, default=None):
    while True:
        name = input(prompt).strip()

        if name:
            return name

        if default is not None:
            return default

        print('Name cannot be empty.')

