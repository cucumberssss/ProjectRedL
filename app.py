import requests
from flask import Flask, render_template, request, flash
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objs as go
from datetime import datetime

ACCUWEATHER_API_KEY = '2ElTS6kcT2RQy8k923d5Ar4QQsJLK8tM'
BASE_URL = 'http://dataservice.accuweather.com/'

app = Flask(__name__)
app.secret_key = 'Sat'

dash_app = dash.Dash(__name__, server=app, url_base_pathname='/dash/')


def get_location_key(city):
    try:
        location_url = f"{BASE_URL}locations/v1/cities/search"
        params = {
            'apikey': ACCUWEATHER_API_KEY,
            'q': city
        }
        response = requests.get(location_url, params=params)
        response.raise_for_status()
        location_data = response.json()
        if not location_data:
            raise ValueError("Город не найден.")
        return location_data[0]['Key']
    except requests.exceptions.RequestException as e:
        raise Exception(f"Ошибка при получении данных о местоположении: {str(e)}")


def get_weather_forecast(location_key, days):
    try:

        if days == 1:
            weather_url = f"{BASE_URL}forecasts/v1/daily/1day/{location_key}"
        elif days == 5:
            weather_url = f"{BASE_URL}forecasts/v1/daily/5day/{location_key}"
        else:  # для 3 дней
            weather_url = f"{BASE_URL}forecasts/v1/daily/5day/{location_key}"

        params = {
            'apikey': ACCUWEATHER_API_KEY,
            'metric': 'true'
        }
        response = requests.get(weather_url, params=params)
        response.raise_for_status()
        data = response.json()


        if days == 3:
            data['DailyForecasts'] = data['DailyForecasts'][:3]

        return data
    except requests.exceptions.RequestException as e:
        raise Exception(f"Ошибка при получении данных о погоде: {str(e)}")


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        city = request.form['city']
        try:
            location_key = get_location_key(city)
            forecast_data = get_weather_forecast(location_key, 5)
            return render_template('index.html', city=city, forecast=forecast_data)
        except ValueError as ve:
            flash(str(ve))
        except Exception as e:
            flash(str(e))
    return render_template('index.html')



dash_app.layout = html.Div([
    html.H1("Прогноз погоды"),
    dcc.Input(id='input-city', type='text', placeholder='Введите город'),
    dcc.Dropdown(
        id='dropdown-days',
        options=[
            {'label': '1 день', 'value': 1},
            {'label': '3 дня', 'value': 3},
            {'label': '5 дней', 'value': 5}
        ],
        value=3,
        clearable=False
    ),
    dcc.Graph(id='weather-graph'),
])


@dash_app.callback(
    Output('weather-graph', 'figure'),
    [Input('input-city', 'value'),
     Input('dropdown-days', 'value')]
)
def update_graph(city, days):
    if not city or not days:
        return go.Figure()

    try:
        location_key = get_location_key(city)
        forecast_data = get_weather_forecast(location_key, days)

        dates = []
        temperatures_max = []
        temperatures_min = []

        for day in forecast_data['DailyForecasts']:
            date = datetime.strptime(day['Date'], "%Y-%m-%dT%H:%M:%S%z")
            dates.append(date.strftime("%Y-%m-%d"))
            temperatures_max.append(day['Temperature']['Maximum']['Value'])
            temperatures_min.append(day['Temperature']['Minimum']['Value'])

        figure = go.Figure()

        figure.add_trace(go.Scatter(
            x=dates,
            y=temperatures_max,
            mode='lines+markers',
            name='Максимальная температура'
        ))
        figure.add_trace(go.Scatter(
            x=dates,
            y=temperatures_min,
            mode='lines+markers',
            name='Минимальная температура'
        ))

        figure.update_layout(
            title=f'Прогноз температуры для {city}',
            xaxis_title='Дата',
            yaxis_title='Температура (°C)',
            hovermode="x unified"
        )

        return figure
    except Exception as e:
        print(f"Ошибка при обновлении графика: {str(e)}")
        return go.Figure()

if __name__ == '__main__':
    app.run(debug=True)


