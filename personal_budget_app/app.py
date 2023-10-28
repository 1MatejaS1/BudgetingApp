from flask import Flask, render_template, request, redirect, url_for #web development / stage 1
import matplotlib.pyplot as plt #plottig / stage 1
import io #conversion / stage 1
import base64 # conversion / stage 1
import yfinance as yf # Yahoo finance stock data / stage 2
import ta # Finance analysis (ta - technical analysis) Simple Moving Average... / stage 3
from ta.utils import dropna #same as above
from datetime import datetime, timedelta #making the stock data universal (year ago to date)  / stage 3
import pandas as pd #stock prediction / future stage 4

app = Flask(__name__) #app begin

expenses = []
budget = 0

@app.route('/')
def index():
    total_expenses = sum(expense[1] for expense in expenses)
    remaining_budget = budget - total_expenses
    yearly_savings = remaining_budget * 12  # Assuming a yearly calculation based on current month's pattern
    expense_percentages = [(expense[0], (expense[1] / total_expenses) * 100) for expense in expenses]

    return render_template('index.html', expenses=expenses, budget=budget, total_expenses=total_expenses,
                           reset_success=False, remaining_budget=remaining_budget, yearly_savings=yearly_savings, expense_percentages=expense_percentages)

@app.template_filter('format_number') # number formatting
def format_number(value):
    return "{:,.2f}".format(value)

@app.route('/add_expense', methods=['POST']) # expense list
def add_expense():
    global expenses
    expense_name = request.form.get('expense_name')
    expense_amount = float(request.form.get('expense_amount'))
    expenses.append((expense_name, expense_amount))
    return redirect(url_for('index'))

@app.route('/set_budget', methods=['POST']) # just setting budget
def set_budget():
    global budget
    budget = float(request.form.get('budget'))
    return redirect(url_for('index'))

@app.route('/reset', methods=['POST']) # reset functionality
def reset():
    global expenses, budget
    expenses = []
    budget = 0
    return redirect(url_for('index'))

@app.route('/savings_graph') # define savings graph parameters
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

@app.route('/stock_prices', methods=['GET', 'POST']) # get stock values from Yahoo
def stock_prices():
    stock_symbol = request.form.get('stock_symbol')
    stock_data = None

    if stock_symbol:
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
        stock_data = yf.download(stock_symbol, start=start_date, end=end_date)['Adj Close']

    return render_template('stock_prices.html', stock_data=stock_data)

@app.route('/technical_indicators', methods=['GET', 'POST']) # calculate stock indicators
def calculate_technical_indicators():
    stock_symbol = request.args.get('stock_symbol')  # Get the stock symbol from request args
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
    stock_data = yf.download(stock_symbol, start=start_date, end=end_date)['Adj Close']
    
    df = stock_data.copy()
    
    # Calculate technical indicators
    sma_indicator = ta.trend.SMAIndicator(df, window=18).sma_indicator()
    bollinger_bands = ta.volatility.BollingerBands(df).bollinger_pband()
    
    # Drop NaN values from SMA and Bollinger Bands
    sma_indicator = sma_indicator.dropna()
    bollinger_bands = bollinger_bands.dropna()
    
    df['SMA'] = sma_indicator
    df['BollingerBands'] = bollinger_bands
    
    return df

@app.route('/ROI', methods=['GET', 'POST']) # calculate return on investment
def ROI():
    stock_symbol = request.args.get('stock_symbol')
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
    stock_data = yf.download(stock_symbol, start=start_date, end=end_date)['Adj Close']

    total_expenses = sum(expense[1] for expense in expenses)
    remaining_budget = budget - total_expenses
    yearly_savings = remaining_budget * 12
 
    shares_initial = yearly_savings // stock_data.iloc[0]
    initial_investment = shares_initial * stock_data.iloc[0]

    final_value = stock_data.iloc[-1]  * shares_initial # Get the last available stock price as the final value
    roi = round(((final_value - initial_investment) / initial_investment * 100), 2)

    return str(roi) + "%"

@app.route('/visualize', methods=['GET', 'POST'])
def visualize():
    total_expenses = sum(expense[1] for expense in expenses)
    remaining_budget = budget - total_expenses
    yearly_savings = remaining_budget * 12  # Assuming a yearly calculation based on the current month's pattern

    labels = [expense[0] for expense in expenses]
    amounts = [expense[1] for expense in expenses]

    plt.figure(figsize=(12, 6))

    plt.subplot(1, 2, 1)
    plt.pie(amounts, labels=labels, autopct='%1.1f%%', startangle=140)
    plt.axis('equal')

    roi = None  # Initialize ROI variable
    chart_url_stock = None  # Initialize stock chart URL variable
    df = None  # Initialize df variable to None

    if 'stock_symbol' in request.args:
        stock_symbol = request.args['stock_symbol']
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
        stock_data = yf.download(stock_symbol, start=start_date, end=end_date)['Adj Close']
        df = calculate_technical_indicators()

        # Calculate ROI using the ROI function directly
        roi = ROI()

        plt.figure(figsize=(6, 3))

        plt.plot(stock_data.index, stock_data, label=stock_symbol, color='black')

        # Calculate Bollinger Bands for the stock_data
        rolling_mean = stock_data.rolling(window=20).mean()
        rolling_std = stock_data.rolling(window=20).std()

        # Plot the Bollinger Bands shading based on rolling_mean and rolling_std
        plt.fill_between(
            stock_data.index,
            rolling_mean - 2 * rolling_std,
            rolling_mean + 2 * rolling_std,
            color='peru', alpha=0.2, label='Bollinger Bands'
        )
        plt.plot(df['SMA'].index, df['SMA'], label='SMA', color='teal')

        plt.xlabel('Date')
        plt.grid(axis='y')
        plt.ylabel('Price ($) / Indicator Value')
        plt.title(f'{stock_symbol} Stock Price 1Y to date')
        plt.legend()

        img = io.BytesIO()
        plt.savefig(img, format='png')
        img.seek(0)
        chart_url_stock = base64.b64encode(img.getvalue()).decode()

        # Calculate percentage of each expense for the pie chart
    expense_percentages = [(expense[0], (expense[1] / total_expenses) * 100) for expense in expenses]

    # Calculate the explode values
    explode_factor = 0.05
    num_expenses = len(expense_percentages)
    explode = [explode_factor] * num_expenses

    # Generate the pie chart
    labels = [expense[0] for expense in expense_percentages]
    percentages = [expense[1] for expense in expense_percentages]

    plt.figure(figsize=(2.5, 2.5))  # Adjust the figure size as needed

    # Create the pie chart
    pie = plt.pie(percentages, labels=labels, autopct='%1.1f%%', startangle=90, pctdistance=0.80, explode=explode, colors=['#0097b2', 'peru', 'coral', 'indianred'], textprops={'fontsize': 8})

    # Create and add a circle to the center of the pie chart
    centre_circle = plt.Circle((0, 0), 0.70, fc='white')
    fig = plt.gcf()
    fig.gca().add_artist(centre_circle)

    # Equal aspect ratio ensures that circle is drawn as a circle.
    plt.axis('equal')

    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    pie_chart = base64.b64encode(img.getvalue()).decode()

    return render_template('index.html', expenses=expenses, budget=budget, total_expenses=total_expenses,
                       reset_success=False, remaining_budget=remaining_budget, yearly_savings=yearly_savings,
                       expense_percentages=expense_percentages, pie_chart=pie_chart, chart_url_stock=chart_url_stock, df=df, roi=roi)

if __name__ == '__main__':
    app.run(debug=True)