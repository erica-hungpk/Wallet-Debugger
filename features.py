import calendar
import csv
import math
import random
from datetime import date

import financial_type as fin

# General input helpers
def input_number(prompt, minimum=None, maximum=None):
    while True:
        try:
            value = float(input(prompt))

            if minimum is not None and value < minimum:
                print(f'Please enter a number greater than or equal to {minimum}.')
                continue

            if maximum is not None and value > maximum:
                print(f'Please enter a number less than or equal to {maximum}.')
                continue

            return value

        except ValueError:
            print('Please enter a valid number.')


def input_integer(prompt, minimum=None, maximum=None):
    while True:
        try:
            value = int(input(prompt))

            if minimum is not None and value < minimum:
                print(f'Please enter an integer greater than or equal to {minimum}.')
                continue

            if maximum is not None and value > maximum:
                print(f'Please enter an integer less than or equal to {maximum}.')
                continue

            return value

        except ValueError:
            print('Please enter a valid integer.')


def yes_no(prompt):
    while True:
        answer = input(prompt).strip().lower()

        if answer in ('y', 'yes'):
            return True

        if answer in ('n', 'no'):
            return False

        print('Please enter Y or N.')


# Date and goal helpers
def add_months(start_date, months):
    """Return a date a given number of calendar months after start_date."""

    month_index = start_date.month - 1 + months
    year = start_date.year + month_index // 12
    month = month_index % 12 + 1

    day = min(
        start_date.day,
        calendar.monthrange(year, month)[1]
    )

    return date(year, month, day)


def months_until(deadline):
    """
    Return the approximate number of monthly contributions remaining.

    A deadline less than one month away still requires one contribution.
    """

    remaining_days = (deadline - date.today()).days

    if remaining_days < 0:
        return 0

    return max(1, math.ceil(remaining_days / 30.4375))


def remove_expired_goals(goals, show_message=True):
    """
    Remove short-term goals after their deadline has passed.

    This is called when the program starts and whenever budget planning is opened.
    """

    today = date.today()
    active_goals = []
    expired_goals = []

    for goal in goals:
        if goal['type'] == 'short':
            deadline = date.fromisoformat(goal['deadline'])

            if deadline < today:
                expired_goals.append(goal)
                continue

        active_goals.append(goal)

    goals[:] = active_goals

    if show_message:
        for goal in expired_goals:
            print(
                f"Short-term goal '{goal['name']}' expired and "
                f"was removed from the active budget."
            )

    return expired_goals


def goal_monthly_requirement(goal):
    if goal['type'] == 'long':
        return goal['amount']

    deadline = date.fromisoformat(goal['deadline'])
    months = months_until(deadline)

    remaining_amount = max(
        0,
        goal['amount'] - goal.get('saved', 0)
    )

    if months == 0:
        return 0

    return remaining_amount / months


# Financial calculation helpers
def monthly_recurring_income(incomes):
    return sum(
        income.amount
        for income in incomes
        if income.recurring
    )


def monthly_expenses(expenses):
    return sum(expense.amount for expense in expenses)


def monthly_debt_repayments(liabilities):
    return sum(liability.repayment for liability in liabilities)


def base_monthly_surplus(incomes, expenses, liabilities):
    return (
        monthly_recurring_income(incomes)
        - monthly_expenses(expenses)
        - monthly_debt_repayments(liabilities)
    )


def available_liquid_assets(assets):
    """
    Only assets with liquidity 1 or 2 are considered available for short-term goal funding.
    """

    return sum(
        asset.amount
        for asset in assets
        if asset.liquidity <= 2
    )

def calculate_proportional_cuts(expenses, required_reduction):
    """
    Distribute a reduction proportionally according to each expense's
    current amount, without reducing any expense below its minimum.

    Returns a list of (expense, cut) tuples.
    """
    if required_reduction <= 0 or not expenses:
        return []

    capacities = {
        expense: max(
            0.0,
            expense.amount - expense.min_amount,
        )
        for expense in expenses
    }

    target = min(
        required_reduction,
        sum(capacities.values()),
    )

    if target <= 0:
        return []

    # Find a common reduction percentage. Expenses that reach their
    # minimum are automatically capped.
    low = 0.0
    high = 1.0

    for _ in range(80):
        percentage = (low + high) / 2

        total_cut = sum(
            min(
                capacities[expense],
                expense.amount * percentage,
            )
            for expense in expenses
        )

        if total_cut < target:
            low = percentage
        else:
            high = percentage

    percentage = high

    cuts = [
        (
            expense,
            min(
                capacities[expense],
                expense.amount * percentage,
            ),
        )
        for expense in expenses
    ]

    # Correct any tiny floating-point difference.
    calculated_total = sum(cut for _, cut in cuts)
    difference = target - calculated_total

    if abs(difference) > 1e-9:
        for index, (expense, cut) in enumerate(cuts):
            available = capacities[expense] - cut

            if difference > 0 and available > 0:
                adjustment = min(difference, available)
                cuts[index] = (expense, cut + adjustment)
                difference -= adjustment

            if abs(difference) <= 1e-9:
                break

    return [
        (expense, cut)
        for expense, cut in cuts
        if cut > 1e-9
    ]

def calculate_expense_reductions(expenses, required_reduction):
    suggestions = []
    total_reduction = 0.0
    remaining = max(0.0, required_reduction)

    eligible_expenses = [
        expense
        for expense in expenses
        if expense.reducible
        and expense.rank > 0 
        and expense.amount > expense.min_amount
    ]

    priorities = sorted({
        expense.rank
        for expense in eligible_expenses
    })

    for priority in priorities:
        if remaining <= 1e-9:
            break

        priority_group = [
            expense
            for expense in eligible_expenses
            if expense.rank == priority
        ]

        cuts = calculate_proportional_cuts(
            priority_group,
            remaining,
        )

        group_reduction = 0.0

        for expense, cut in cuts:
            new_amount = expense.amount - cut

            suggestions.append({
                "name": expense.name,
                "current": expense.amount,
                "minimum": expense.min_amount,
                "cut": cut,
                "new_amount": new_amount,
                "rank": expense.rank,
            })

            group_reduction += cut

        total_reduction += group_reduction
        remaining -= group_reduction

    # Avoid returning tiny floating-point residuals.
    if abs(remaining) <= 1e-9:
        remaining = 0.0

    return suggestions, total_reduction, remaining


def calculate_asset_sources(assets, required_amount):
    """
    Suggest which liquid assets can be used.

    The original asset values are not changed. This is only a proposed allocation.
    """

    remaining = max(0, required_amount)
    allocations = []

    liquid_assets = sorted(
        (
            asset for asset in assets
            if asset.liquidity <= 2 and asset.amount > 0
        ),
        key=lambda asset: asset.liquidity
    )

    for asset in liquid_assets:
        if remaining <= 0:
            break

        allocation = min(asset.amount, remaining)

        allocations.append({
            'name': asset.name,
            'amount': allocation,
            'liquidity': asset.liquidity
        })

        remaining -= allocation

    return allocations, remaining


# Budget planning
def display_budget_plan(
    assets,
    liabilities,
    incomes,
    expenses,
    goals
):
    remove_expired_goals(goals)

    income = monthly_recurring_income(incomes)
    regular_expenses = monthly_expenses(expenses)
    repayments = monthly_debt_repayments(liabilities)
    starting_surplus = income - regular_expenses - repayments

    long_goals = [
        goal for goal in goals
        if goal['type'] == 'long'
    ]

    short_goals = sorted(
        (
            goal for goal in goals
            if goal['type'] == 'short'
        ),
        key=lambda goal: goal['deadline']
    )

    long_requirement = sum(
        goal_monthly_requirement(goal)
        for goal in long_goals
    )

    short_requirement = sum(
        goal_monthly_requirement(goal)
        for goal in short_goals
    )

    total_requirement = long_requirement + short_requirement

    required_reduction = max(
        0,
        total_requirement - starting_surplus
    )

    reductions, total_reduction, _ = calculate_expense_reductions(
        expenses,
        required_reduction
    )

    adjusted_surplus = starting_surplus + total_reduction

    print('\n================ MONTHLY BUDGET PLAN ================')
    print(f'Monthly recurring income:       ${income:>12,.2f}')
    print(f'Regular monthly expenses:       ${regular_expenses:>12,.2f}')
    print(f'Monthly debt repayments:        ${repayments:>12,.2f}')
    print('-----------------------------------------------------')
    print(f'Current monthly surplus:        ${starting_surplus:>12,.2f}')
    print(f'Long-term goal requirement:     ${long_requirement:>12,.2f}')
    print(f'Short-term goal requirement:    ${short_requirement:>12,.2f}')
    print(f'Total monthly goal requirement: ${total_requirement:>12,.2f}')

    if reductions:
        print('\nSuggested expense reductions:')

        for reduction in reductions:
            print(
                f"  {reduction['name']}: "
                f"${reduction['current']:,.2f} -> "
                f"${reduction['new_amount']:,.2f} "
                f"(save ${reduction['cut']:,.2f}, "
                f"priority {reduction['rank']})"
            )
    else:
        print('\nNo expense reductions are required or available.')

    print(
        f'\nSurplus after suggested cuts:   '
        f'${adjusted_surplus:>12,.2f}'
    )

    # Allocate sustainable monthly cash flow to long-term goals first.
    remaining_monthly_cash = max(0, adjusted_surplus)

    print('\nGoal allocations:')

    long_term_unfunded = 0

    for goal in long_goals:
        required = goal_monthly_requirement(goal)
        allocated = min(required, remaining_monthly_cash)
        shortage = required - allocated

        remaining_monthly_cash -= allocated
        long_term_unfunded += shortage

        print(
            f"  [Long-term] {goal['name']}: "
            f"${allocated:,.2f} of ${required:,.2f} per month"
        )

    # Allocate remaining monthly cash flow to short-term goals.
    short_term_asset_requirement = 0

    for goal in short_goals:
        required = goal_monthly_requirement(goal)
        months = months_until(date.fromisoformat(goal['deadline']))

        monthly_allocation = min(required, remaining_monthly_cash)
        remaining_monthly_cash -= monthly_allocation

        monthly_shortage = required - monthly_allocation
        asset_requirement = monthly_shortage * months

        short_term_asset_requirement += asset_requirement

        print(
            f"  [Short-term] {goal['name']}: "
            f"${monthly_allocation:,.2f} of ${required:,.2f} per month, "
            f"{months} month(s) remaining"
        )

    asset_allocations, uncovered_asset_amount = calculate_asset_sources(
        assets,
        short_term_asset_requirement
    )

    if asset_allocations:
        print('\nSuggested one-time liquid-asset allocation:')

        for allocation in asset_allocations:
            print(
                f"  {allocation['name']}: "
                f"${allocation['amount']:,.2f}"
            )

        print(
            'Warning: using liquid assets will reduce your '
            'emergency reserve.'
        )

    print('\nPlan status:')

    if long_term_unfunded > 0:
        print(
            f'  ALERT: Long-term goals are short by '
            f'${long_term_unfunded:,.2f} per month.'
        )

    if uncovered_asset_amount > 0:
        print(
            f'  ALERT: Short-term goals are still short by '
            f'${uncovered_asset_amount:,.2f}.'
        )

    if not goals:
        print('  No savings goals have been created.')

    elif long_term_unfunded == 0 and uncovered_asset_amount == 0:
        print('  All active goals are achievable under this plan.')

    print('=====================================================\n')


def add_long_term_goal(goals):
    print('\n--- Add Long-Term Savings Goal ---')

    name = input('Goal name: ').strip()

    if not name:
        name = 'Long-Term Savings'

    monthly_amount = input_number(
        'Amount to save every month: $',
        minimum=0.01
    )

    goals.append({
        'name': name,
        'type': 'long',
        'amount': monthly_amount,
        'deadline': '',
        'saved': 0.0
    })

    print(f"Long-term goal '{name}' was added.\n")


def add_short_term_goal(goals):
    print('\n--- Add Short-Term Goal ---')

    name = input('Goal name: ').strip()

    if not name:
        name = 'Short-Term Goal'

    target = input_number(
        'Total target amount: $',
        minimum=0.01
    )

    saved = input_number(
        'Amount already saved: $',
        minimum=0,
        maximum=target
    )

    months = input_integer(
        'Number of months until the deadline: ',
        minimum=1
    )

    deadline = add_months(date.today(), months)

    goals.append({
        'name': name,
        'type': 'short',
        'amount': target,
        'deadline': deadline.isoformat(),
        'saved': saved
    })

    print(
        f"Short-term goal '{name}' was added with a deadline of "
        f"{deadline.isoformat()}.\n"
    )


def record_goal_contribution(goals):
    short_goals = [
        goal for goal in goals
        if goal['type'] == 'short'
    ]

    if not short_goals:
        print('There are no short-term goals to update.')
        return

    print('\nShort-term goals:')

    for index, goal in enumerate(short_goals, start=1):
        print(
            f"{index}: {goal['name']} - "
            f"${goal.get('saved', 0):,.2f} saved of "
            f"${goal['amount']:,.2f}"
        )

    selection = input_integer(
        'Select a goal: ',
        minimum=1,
        maximum=len(short_goals)
    )

    goal = short_goals[selection - 1]
    remaining = max(0, goal['amount'] - goal.get('saved', 0))

    if remaining == 0:
        print('This goal is already fully funded.')
        return

    contribution = input_number(
        'Contribution amount: $',
        minimum=0.01,
        maximum=remaining
    )

    goal['saved'] = goal.get('saved', 0) + contribution

    print(
        f"Contribution recorded. '{goal['name']}' now has "
        f"${goal['saved']:,.2f} saved."
    )


def remove_goal(goals):
    if not goals:
        print('There are no goals to remove.')
        return

    print('\nActive goals:')

    for index, goal in enumerate(goals, start=1):
        if goal['type'] == 'long':
            description = f"${goal['amount']:,.2f}/month"
        else:
            description = (
                f"${goal['amount']:,.2f} by {goal['deadline']}"
            )

        print(f'{index}: {goal["name"]} - {description}')

    selection = input_integer(
        'Select a goal to remove: ',
        minimum=1,
        maximum=len(goals)
    )

    removed = goals.pop(selection - 1)
    print(f"Goal '{removed['name']}' was removed.")


def budget_planning(
    assets,
    liabilities,
    incomes,
    expenses,
    goals
):
    remove_expired_goals(goals)

    while True:
        print(
            '\n'
            '--------------- Budget Planning ---------------\n'
            '1: Add long-term monthly savings goal\n'
            '2: Add short-term goal\n'
            '3: Record a contribution to a short-term goal\n'
            '4: View budget plan\n'
            '5: Remove a goal\n'
            '6: Return to main menu\n'
        )

        choice = input_integer('Function: ', 1, 6)

        if choice == 1:
            add_long_term_goal(goals)
            display_budget_plan(
                assets,
                liabilities,
                incomes,
                expenses,
                goals
            )

        elif choice == 2:
            add_short_term_goal(goals)
            display_budget_plan(
                assets,
                liabilities,
                incomes,
                expenses,
                goals
            )

        elif choice == 3:
            record_goal_contribution(goals)

        elif choice == 4:
            display_budget_plan(
                assets,
                liabilities,
                incomes,
                expenses,
                goals
            )

        elif choice == 5:
            remove_goal(goals)

        elif choice == 6:
            break


# Financial simulator
def financial_simulator(assets, liabilities, incomes, expenses, goals):
    remove_expired_goals(goals)

    print('\n========== FINANCIAL SIMULATION TEST ==========')
    print(
        'Enter hypothetical changes. These values will not modify '
        'your real financial information.\n'
    )

    income_change = input_number(
        'Monthly income change (use a negative number for a loss): $'
    )

    expense_change = input_number(
        'Monthly expense change: $'
    )

    asset_value_change = input_number(
        'Change in asset values (%): ',
        minimum=-100
    )

    one_time_emergency = input_number(
        'One-time emergency cost: $',
        minimum=0
    )

    salary_raise = input_number(
        'Expected monthly salary increase: $',
        minimum=0
    )

    lifestyle_percentage = input_number(
        'Percentage of the raise spent on lifestyle inflation: ',
        minimum=0,
        maximum=100
    )

    current_income = monthly_recurring_income(incomes)
    current_expenses = (
        monthly_expenses(expenses)
        + monthly_debt_repayments(liabilities)
    )

    lifestyle_increase = (
        salary_raise * lifestyle_percentage / 100
    )

    projected_income = current_income + income_change + salary_raise

    projected_expenses = (
        current_expenses
        + expense_change
        + lifestyle_increase
    )

    projected_surplus = projected_income - projected_expenses

    current_asset_value = sum(asset.amount for asset in assets)

    projected_asset_value = (
        current_asset_value
        * (1 + asset_value_change / 100)
        - one_time_emergency
    )

    projected_asset_value = max(0, projected_asset_value)

    liquid_assets = available_liquid_assets(assets)
    liquid_after_emergency = max(
        0,
        liquid_assets - one_time_emergency
    )

    if projected_expenses > 0:
        emergency_runway = (
            liquid_after_emergency / projected_expenses
        )
    else:
        emergency_runway = math.inf

    total_goal_requirement = sum(
        goal_monthly_requirement(goal)
        for goal in goals
    )

    print('\n--------------- Simulation-Test Result ---------------')
    print(f'Projected monthly income:       ${projected_income:>12,.2f}')
    print(f'Projected monthly expenses:     ${projected_expenses:>12,.2f}')
    print(f'Projected monthly surplus:      ${projected_surplus:>12,.2f}')
    print(f'Projected total asset value:    ${projected_asset_value:>12,.2f}')
    print(f'Liquid assets after emergency:  ${liquid_after_emergency:>12,.2f}')
    print(f'Lifestyle inflation increase:   ${lifestyle_increase:>12,.2f}')

    if math.isinf(emergency_runway):
        print('Emergency-fund runway:          Unlimited')
    else:
        print(
            f'Emergency-fund runway:          '
            f'{emergency_runway:>12.1f} months'
        )

    print('\nAssessment:')

    if projected_surplus < 0:
        print(
            f'  ALERT: You would lose '
            f'${abs(projected_surplus):,.2f} each month.'
        )
    else:
        print(
            f'  You would retain '
            f'${projected_surplus:,.2f} each month.'
        )

    if projected_surplus < total_goal_requirement:
        shortage = total_goal_requirement - projected_surplus
        print(
            f'  ALERT: Your active goals would be underfunded by '
            f'${shortage:,.2f} per month.'
        )
    else:
        print('  Your active monthly goal requirements remain funded.')

    if lifestyle_percentage >= 75:
        print(
            '  Warning: most of the salary increase is being consumed '
            'by lifestyle inflation.'
        )

    if not math.isinf(emergency_runway) and emergency_runway < 3:
        print(
            '  Warning: the remaining emergency fund covers fewer '
            'than three months of expenses.'
        )

    print('==================================================\n')


# Opportunity cost visualiser
def weighted_investment_return(assets):
    investments = [
        asset for asset in assets
        if asset.return_rate > 0
        and asset.amount > 0
        and asset.name.strip().lower() != 'cash'
    ]

    total = sum(asset.amount for asset in investments)

    if total == 0:
        return 0.05

    return sum(
        asset.amount * asset.return_rate
        for asset in investments
    ) / total


# Opportunity Cost Visualiser Helpers
def format_cost_quantity(quantity):
    """Format an everyday-equivalent quantity."""

    if quantity < 1:
        return f'{quantity:,.2f}'

    if quantity < 10:
        return f'{quantity:,.1f}'

    return f'{quantity:,.0f}'


def everyday_cost_translation(
    amount,
    unit_price,
    singular,
    plural,
    comment
):
    """Convert an amount of money into an everyday equivalent."""

    if unit_price <= 0:
        raise ValueError('comparison unit price must be greater than zero')

    quantity = amount / unit_price
    quantity_text = format_cost_quantity(quantity)

    # Use singular only when the result is approximately one.
    label = singular if 0.95 <= quantity <= 1.05 else plural

    return (
        f'{quantity_text} {label} — {comment}'
    )


def opportunity_cost_visualiser(assets, liabilities, incomes, expenses, goals, prices=None):
    remove_expired_goals(goals)

    print('\n========== OPPORTUNITY COST VISUALISER ==========')

    purchase_name = input('Potential purchase: ').strip()

    if not purchase_name:
        purchase_name = 'Purchase'

    price = input_number(
        'Purchase price: $',
        minimum=0.01
    )

    expected_uses = input_integer(
        'Expected number of uses: ',
        minimum=1
    )

    investment_years = input_integer(
        'Investment comparison period in years: ',
        minimum=1
    )

    # These are example prices. Change them to match local prices.
    comparison_prices = {
        'meal': 15.00,
        'youtube_premium_month': 13.99,
        'netflix_month': 15.49,
        'pizza': 18.00,
        'uber_ride': 22.00,
        'coffee': 5.50,
        'bubble_tea': 7.00,
        'movie_ticket': 16.00,
        'video_game': 70.00,
        'ramen_packet': 1.50,
        'taco': 3.50,
        'ice_cream': 5.00,
        'laundry_load': 4.00,
        'toilet_paper_roll': 1.25,
        'banana': 0.30,
        'fancy_candle': 25.00,
        'haircut': 30.00,
        'parking_hour': 4.00,
        'grocery_week': 100.00,
        'date_night': 75.00,
        'book': 18.00,
        'gym_month': 35.00,
        'phone_bill_month': 60.00,
        'internet_month': 70.00
    }

    # Optional custom/local prices override the defaults.
    if prices is not None:
        for item, item_price in prices.items():
            if item not in comparison_prices:
                raise ValueError(
                    f'unknown cost comparison item: {item!r}'
                )

            item_price = float(item_price)

            if item_price <= 0:
                raise ValueError(
                    f'price for {item!r} must be greater than zero'
                )

            comparison_prices[item] = item_price

    monthly_income = monthly_recurring_income(incomes)

    monthly_surplus = base_monthly_surplus(
        incomes,
        expenses,
        liabilities
    )

    # Assumes approximately 160 working hours per month.
    hourly_income = (
        monthly_income / 160
        if monthly_income > 0
        else 0
    )

    cash = sum(
        asset.amount
        for asset in assets
        if asset.liquidity == 1
    )

    total_goal_requirement = sum(
        goal_monthly_requirement(goal)
        for goal in goals
    )

    investment_rate = weighted_investment_return(assets)

    if hourly_income > 0:
        work_hours = price / hourly_income

        work_hours_text = (
            f'Work time: approximately {work_hours:,.1f} hours '
            f'of income. Your wallet measures this purchase in '
            f'pieces of your working life.'
        )
    else:
        work_hours_text = (
            'Work time cannot be calculated because recurring '
            'income is zero.'
        )

    if monthly_surplus > 0:
        savings_months = price / monthly_surplus

        savings_months_text = (
            f'Savings time: approximately {savings_months:,.1f} '
            f'months of your current monthly surplus.'
        )
    else:
        savings_months_text = (
            'Savings time: this purchase cannot currently be funded '
            'from your monthly cash-flow surplus.'
        )

    if total_goal_requirement > 0:
        goal_delay = price / total_goal_requirement

        goal_delay_text = (
            f'Goal impact: the price equals approximately '
            f'{goal_delay:,.1f} months of planned goal contributions.'
        )
    else:
        goal_delay_text = (
            'Goal impact: there are no active savings goals '
            'available for comparison.'
        )

    if cash > 0:
        emergency_percentage = price / cash * 100

        emergency_text = (
            f'Cash-reserve impact: this purchase would consume '
            f'{emergency_percentage:,.1f}% of the money in your '
            f"assets with liquidity = 1."
        )
    else:
        emergency_text = (
            "Cash-reserve impact cannot be calculated because you "
            "currently have no asset with liquidity = 1."
        )

    future_value = price * (
        (1 + investment_rate) ** investment_years
    )

    lost_growth = future_value - price

    investment_text = (
        f'Investment opportunity cost: ${price:,.2f} invested at '
        f'{investment_rate * 100:,.2f}% could become '
        f'${future_value:,.2f} after {investment_years} year(s). '
        f'The estimated growth given up is ${lost_growth:,.2f}.'
    )

    cost_per_use = price / expected_uses

    cost_per_use_text = (
        f'Cost per use: ${cost_per_use:,.2f} across '
        f'{expected_uses:,} expected uses.'
    )

    financial_translations = [
        work_hours_text,
        savings_months_text,
        goal_delay_text,
        emergency_text,
        investment_text,
        cost_per_use_text
    ]

    # Everyday-life translations
    everyday_items = [
        (
            'meal',
            'meal',
            'meals',
            'Enough food to avoid calling sleep a meal.'
        ),
        (
            'youtube_premium_month',
            'month of YouTube Premium',
            'months of YouTube Premium',
            'That represents many ads you would never have to watch.'
        ),
        (
            'netflix_month',
            'month of Netflix',
            'months of Netflix',
            'Plenty of time to spend 40 minutes choosing what to watch.'
        ),
        (
            'pizza',
            'pizza',
            'pizzas',
            'Financial planning, but with extra cheese.'
        ),
        (
            'uber_ride',
            'Uber ride',
            'Uber rides',
            'Surge pricing may have other plans.'
        ),
        (
            'coffee',
            'cup of coffee',
            'cups of coffee',
            'Enough caffeine to make another budget spreadsheet.'
        ),
        (
            'bubble_tea',
            'bubble tea',
            'bubble teas',
            'A highly liquid investment.'
        ),
        (
            'movie_ticket',
            'movie ticket',
            'movie tickets',
            'Popcorn and emotional damage are sold separately.'
        ),
        (
            'video_game',
            'new video game',
            'new video games',
            'Your unfinished game library is already judging you.'
        ),
        (
            'ramen_packet',
            'packet of ramen',
            'packets of ramen',
            'The unofficial currency of university students.'
        ),
        (
            'taco',
            'taco',
            'tacos',
            'A deliciously diversified salsa portfolio.'
        ),
        (
            'ice_cream',
            'ice cream',
            'ice creams',
            'A delicious but rapidly melting asset.'
        ),
        (
            'laundry_load',
            'load of laundry',
            'loads of laundry',
            'Enough clean socks to become truly powerful.'
        ),
        (
            'toilet_paper_roll',
            'roll of toilet paper',
            'rolls of toilet paper',
            'A surprisingly practical emergency fund.'
        ),
        (
            'banana',
            'banana',
            'bananas',
            'There is always money in the banana stand.'
        ),
        (
            'fancy_candle',
            'fancy candle',
            'fancy candles',
            'Your money can literally go up in smoke.'
        ),
        (
            'haircut',
            'haircut',
            'haircuts',
            'Unlike some financial decisions, the hair grows back.'
        ),
        (
            'parking_hour',
            'hour of parking',
            'hours of parking',
            'Paying your car to stand completely still.'
        ),
        (
            'grocery_week',
            'week of groceries',
            'weeks of groceries',
            'Less exciting than shopping, but considerably more edible.'
        ),
        (
            'date_night',
            'date night',
            'date nights',
            'Romance is temporary; the card statement is permanent.'
        ),
        (
            'book',
            'book',
            'books',
            'An investment in knowledge—or an impressive unread pile.'
        ),
        (
            'gym_month',
            'month of gym membership',
            'months of gym membership',
            'Actual attendance is unfortunately not included.'
        ),
        (
            'phone_bill_month',
            'monthly phone bill',
            'monthly phone bills',
            'A small price to pay for receiving spam calls.'
        ),
        (
            'internet_month',
            'month of internet',
            'months of internet',
            'Essential infrastructure for sending memes.'
        )
    ]

    everyday_translations = []

    for (
        price_key,
        singular,
        plural,
        comment
    ) in everyday_items:
        everyday_translations.append(
            everyday_cost_translation(
                amount=price,
                unit_price=comparison_prices[price_key],
                singular=singular,
                plural=plural,
                comment=comment
            )
        )

    # Results
    print(f'\nOpportunity costs for {purchase_name}:')
    print(f'Purchase price: ${price:,.2f}')
    print('--------------------------------------------------')

    random.shuffle(everyday_translations)
    translation_index = 0

    while True:
        if translation_index + 2 > len(everyday_translations):
            random.shuffle(everyday_translations)
            translation_index = 0
            print('All everyday comparisons have been shown. Reshuffling!')

        everyday_selection = everyday_translations[
            translation_index:translation_index + 2
        ]

        translation_index += 2

        selected = [
            random.choice(financial_translations),
            *everyday_selection
        ]

        random.shuffle(selected)

        for number, translation in enumerate(selected, start=1):
            print(f'{number}. {translation}')

        print('--------------------------------------------------')

        if not yes_no(
            'Show another set of three translations (Y/N)? '
        ):
            break

        print('--------------------------------------------------')

    print('=================================================\n')

# file exporting
def export_financial_data(
    filename,
    assets,
    liabilities,
    incomes,
    expenses,
    goals
):
    remove_expired_goals(goals, show_message=False)

    try:
        with open(
            filename,
            'w',
            encoding='utf-8',
            newline=''
        ) as file:

            writer = csv.writer(
                file,
                delimiter='|',
                lineterminator='\n'
            )

            writer.writerow(['[Assets]'])

            for asset in assets:
                writer.writerow([
                    asset.name,
                    asset.amount,
                    asset.liquidity,
                    asset.return_rate * 100
                ])

            writer.writerow(['[Liabilities]'])

            for liability in liabilities:
                writer.writerow([
                    liability.name,
                    liability.amount,
                    liability.interest * 100,
                    liability.repayment
                ])

            writer.writerow(['[Incomes]'])

            for income in incomes:
                writer.writerow([
                    income.name,
                    income.amount,
                    income.recurring
                ])

            writer.writerow(['[Expenses]'])

            for expense in expenses:
                writer.writerow([
                    expense.name,
                    expense.amount,
                    expense.reducible,
                    expense.min_amount,
                    expense.rank
                ])

            writer.writerow(['[Goals]'])

            for goal in goals:
                writer.writerow([
                    goal['name'],
                    goal['type'],
                    goal['amount'],
                    goal.get('deadline', ''),
                    goal.get('saved', 0)
                ])

    except OSError as error:
        print(f'Unable to export {filename}: {error}')
        return False

    print(f'Financial data was exported to {filename}.')
    print('')

    return True


# file input loading
def parse_boolean(value):
    value = value.strip().lower()

    if value == 'true':
        return True

    if value == 'false':
        return False

    raise ValueError(
        f"expected 'True' or 'False', received {value!r}"
    )


def load_financial_data(filename):
    sections = {
        '[Assets]': [],
        '[Liabilities]': [],
        '[Incomes]': [],
        '[Expenses]': [],
        '[Goals]': []
    }

    current_section = None

    try:
        with open(
            filename,
            'r',
            encoding='utf-8',
            newline=''
        ) as file:

            reader = csv.reader(file, delimiter='|')

            for row in reader:
                line_number = reader.line_num
                row = [field.strip() for field in row]

                if not row or all(field == '' for field in row):
                    continue

                if len(row) == 1 and row[0] in sections:
                    current_section = row[0]
                    continue

                if current_section is None:
                    raise ValueError(
                        f'line {line_number}: data appears before '
                        f'a valid section heading'
                    )

                try:
                    if current_section == '[Assets]':
                        if len(row) != 4:
                            raise ValueError(
                                'an asset requires 4 fields'
                            )

                        name, amount, liquidity, return_rate = row

                        sections[current_section].append(
                            fin.Assets(
                                name,
                                float(amount),
                                int(liquidity),
                                float(return_rate)
                            )
                        )

                    elif current_section == '[Liabilities]':
                        if len(row) != 4:
                            raise ValueError(
                                'a liability requires 4 fields'
                            )

                        name, amount, interest, repayment = row

                        sections[current_section].append(
                            fin.Liabilities(
                                name,
                                float(amount),
                                float(interest),
                                float(repayment)
                            )
                        )

                    elif current_section == '[Incomes]':
                        if len(row) != 3:
                            raise ValueError(
                                'an income requires 3 fields'
                            )

                        name, amount, recurring = row

                        sections[current_section].append(
                            fin.Incomes(
                                name,
                                float(amount),
                                parse_boolean(recurring)
                            )
                        )

                    elif current_section == '[Expenses]':
                        if len(row) != 5:
                            raise ValueError(
                                'an expense requires 5 fields'
                            )

                        name, amount, reducible, minimum, rank = row

                        sections[current_section].append(
                            fin.Expenses(
                                name,
                                float(amount),
                                parse_boolean(reducible),
                                float(minimum),
                                int(rank)
                            )
                        )

                    elif current_section == '[Goals]':
                        if len(row) != 5:
                            raise ValueError(
                                'a goal requires 5 fields'
                            )

                        name, goal_type, amount, deadline, saved = row

                        name = name.strip()
                        goal_type = goal_type.strip().lower()
                        amount = float(amount)
                        saved = float(saved)

                        if not name:
                            raise ValueError('goal name cannot be empty')

                        if goal_type not in ('long', 'short'):
                            raise ValueError(
                                "goal type must be 'long' or 'short'"
                            )

                        if not math.isfinite(amount) or amount <= 0:
                            raise ValueError(
                                'goal amount must be a finite number greater than zero'
                            )

                        if not math.isfinite(saved) or saved < 0:
                            raise ValueError(
                                'saved amount must be a finite nonnegative number'
                            )

                        if goal_type == 'long':
                            if deadline:
                                raise ValueError(
                                    'a long-term goal cannot have a deadline'
                                )

                            if saved != 0:
                                raise ValueError(
                                    'a long-term monthly goal cannot have a saved balance'
                                )

                        else:
                            if not deadline:
                                raise ValueError(
                                    'a short-term goal must have a deadline'
                                )

                            date.fromisoformat(deadline)

                            if saved > amount:
                                raise ValueError(
                                    'saved amount cannot exceed the goal target'
                                )

                        sections[current_section].append({
                            'name': name,
                            'type': goal_type,
                            'amount': amount,
                            'deadline': deadline,
                            'saved': saved
                        })

                except ValueError as error:
                    raise ValueError(
                        f'line {line_number}: {error}'
                    ) from error

    except OSError as error:
        raise OSError(
            f'Unable to open {filename}: {error}'
        ) from error

    assets = sections['[Assets]']
    liabilities = sections['[Liabilities]']
    incomes = sections['[Incomes]']
    expenses = sections['[Expenses]']
    goals = sections['[Goals]']

    remove_expired_goals(goals, show_message=False)

    return assets, liabilities, incomes, expenses, goals
