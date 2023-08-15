from flask import Flask, render_template, request, redirect, url_for
import matplotlib.pyplot as plt
import io
import base64

app = Flask(__name__)

expenses = []
budget = 0

@app.route('/')
def index():
    total_expenses = sum(expense[1] for expense in expenses)
    remaining_budget = budget - total_expenses
    yearly_savings = remaining_budget * 12  # Assuming a yearly calculation based on current month's pattern
    return render_template('index.html', expenses=expenses, budget=budget, total_expenses=total_expenses,
                           reset_success=False, remaining_budget=remaining_budget, yearly_savings=yearly_savings)

@app.template_filter('format_number')
def format_number(value):
    return "{:,.2f}".format(value)


@app.route('/add_expense', methods=['POST'])
def add_expense():
    global expenses
    expense_name = request.form.get('expense_name')
    expense_amount = float(request.form.get('expense_amount'))
    expenses.append((expense_name, expense_amount))
    return redirect(url_for('index'))

@app.route('/set_budget', methods=['POST'])
def set_budget():
    global budget
    budget = float(request.form.get('budget'))
    return redirect(url_for('index'))

@app.route('/visualize')
def visualize():
    labels = [expense[0] for expense in expenses]
    amounts = [expense[1] for expense in expenses]
    plt.figure(figsize=(8, 6))
    plt.pie(amounts, labels=labels, autopct='%1.1f%%', startangle=140)
    plt.axis('equal')
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    chart_url = base64.b64encode(img.getvalue()).decode()
    return render_template('budget.html', chart_url=chart_url)

@app.route('/reset', methods=['POST'])
def reset():
    global expenses, budget
    expenses = []
    budget = 0
    return redirect(url_for('index'))

@app.route('/savings_graph')
def savings_graph():
    total_expenses = sum(expense[1] for expense in expenses)
    remaining_budget = budget - total_expenses
    yearly_savings = remaining_budget * 12  # Assuming a yearly calculation based on current month's pattern

    years = list(range(1, 6))
    savings_increase = [yearly_savings * year for year in years]  # Increase by the yearly_savings value each year

    plt.figure(figsize=(8, 4))
    plt.plot(years, savings_increase, marker='o')
    plt.xlabel('Years')
    plt.ylabel('Savings Increase ($)')
    plt.title('5-Year Savings Increase')

    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)

    graph_url = base64.b64encode(img.getvalue()).decode()

    return render_template('savings_graph.html', graph_url=graph_url)


if __name__ == '__main__':
    app.run(debug=True)
