from bs4 import BeautifulSoup
import requests
import sqlite3
from dash import Dash, html, dcc, Output, Input

import plotly.graph_objects as go
import pandas as pd

app = Dash(__name__)

server = app.server

server = app.server


con = sqlite3.connect("hr")


data_employee_job = pd.read_sql("SELECT employees.first_name, jobs.job_title " +
                                "FROM employees " +
                                "INNER JOIN jobs ON employees.job_id " +
                                "= jobs.job_id", con)


def scrape_data():
    URL = "https://www.itjobswatch.co.uk/jobs/uk/sqlite.do"
    r = requests.get(URL)
    soup = BeautifulSoup(r.content, 'html5lib')
    table = soup.find('table', attrs={'class': 'summary'})
    table.find('form').decompose()
    table_data = table.tbody.find_all("tr")
    table = []
    for i in table_data:
        row = []
        rrr = i.find_all("td")
        if len(rrr) == 0:
            rrr = i.find_all("th")
        for j in rrr:
            row.append(j.text)
        table.append(row)

    hd = table[1]
    hd[0] = "index"
    employee_sal = pd.read_sql("SELECT employees.salary " +
                               "FROM employees", con)
    avg_salary = employee_sal['salary'].mean()
    df = pd.DataFrame(table)
    df.drop(index=[0, 1, 2, 3, 4, 5, 6, 7, 10,
            11, 14, 15], axis=0, inplace=True)
    df.columns = hd
    df.set_index("index", inplace=True)
    df.reset_index(inplace=True)
    df['Same period 2021'] = df['Same period 2021'].str.replace('£', '')
    df['Same period 2021'] = df['Same period 2021'].str.replace(',', '')
    df['Same period 2021'] = df['Same period 2021'].str.replace(
        '-', '0').astype(float)
    df['6 months to20 Dec 2022'] = df['6 months to20 Dec 2022'].str.replace(
        '£', '')
    df['6 months to20 Dec 2022'] = df['6 months to20 Dec 2022'].str.replace(
        ',', '').astype(float)
    df['Same period 2020'] = df['Same period 2020'].str.replace('£', '')
    df['Same period 2020'] = df['Same period 2020'].str.replace(
        ',', '').astype(float)

    df.loc[4] = ['Average', avg_salary, avg_salary, avg_salary]

    return df


forth = scrape_data()

axis = forth["index"]
forth.drop("index", inplace=True, axis=1)
# print(axis)
# print(forth)
years = forth.columns
# print(years)


job_count = data_employee_job.groupby('job_title').count().reset_index()
job_count.columns = ["Job Title", "Count"]
jobs = job_count["Job Title"]

jobs_salary_main = pd.read_sql(
    "SELECT job_title, min_salary, max_salary FROM jobs", con)
jobs_salary_main.drop(index=0, axis=0, inplace=True)
jobs_salary_main["difference"] = jobs_salary_main["max_salary"] - \
    jobs_salary_main["min_salary"]

jobs_salary = jobs_salary_main


def update_dataframe(list_of_jobs):
    global job_count
    job_count = data_employee_job.groupby('job_title').count().reset_index()
    job_count.columns = ["Job Title", "Count"]

    if list_of_jobs != "all" and len(list_of_jobs) != 0:
        job_count = job_count[job_count["Job Title"].isin(list_of_jobs)]


def update_dataframe1(minimum, maximum):
    # print("you are in datafrME111")
    global jobs_salary
    global jobs_salary_main
    # # jobs_salary = pd.read_sql("SELECT job_title, min_salary, max_salary FROM jobs",con)
    # print("database done")
    # jobs_salary.drop(index = 0, axis = 0, inplace = True)
    # jobs_salary["difference"] = jobs_salary["max_salary"] - jobs_salary["min_salary"]
    jobs_salary = jobs_salary_main
    diff = maximum - minimum
    jobs_salary = jobs_salary[jobs_salary["difference"] <= diff]


def update_dataframe3(year):
    return forth[year]

    #


app.layout = html.Div(
    [
        html.H1("Human Resouces - Dashboard", className="header"),
        html.Div([
            html.Div("List of jobs", className="joblistlabel"),
            dcc.Dropdown(jobs,
                         multi=True,
                         value='all',
                         placeholder="All",
                         id="input1"
                         ),
        ], className="joblist"),
        dcc.Graph(id="output1"),
        html.Div([
            html.Div([
                html.Div("Minimum", className="minimum"),
                dcc.Slider(0, 30000, 1000,
                           value=1000,
                           id='minimum'
                           ),], className="sliders"),
            html.Div([
                html.Div("Maximum", className="maximum"),
                dcc.Slider(0, 30000, 1000,
                           value=20000,
                           id='maximum'
                           ),], className="sliders"),], className="sliderss"),

        dcc.Graph(id="output2"),
        html.Div([
            html.Div("Choose a Year:   "),
            dcc.Dropdown(years,

                         value='all',
                         placeholder="6 months to20 Dec 2022",
                         id="years"
                         ),
        ],className="years"),
        dcc.Graph(id="output3"),

    ]
)


@app.callback(
    Output('output1', 'figure'),

    Input('input1', 'value')
)
def update_output(value1):

    update_dataframe(value1)

    fig = go.Figure()
    fig.add_trace(go.Bar(x=job_count["Job Title"], y=job_count["Count"])
                  )
    return fig


@app.callback(
    Output('output2', 'figure'),
    [
        Input('minimum', 'value'),
        Input('maximum', 'value'),
    ]
)
def update_output(value1, value2):

    # update_dataframe(value1)
    update_dataframe1(value1, value2)
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=jobs_salary["difference"], y=jobs_salary["job_title"], orientation="h"))

    return fig


@app.callback(
    Output('output3', 'figure'),
    Input('years', 'value')
)
def update_output(value1):
    if value1 == "all" or value1 == None:
        y = forth["6 months to20 Dec 2022"]
    else:
        y = update_dataframe3(value1)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=axis.values, y=y.values))

    return fig


if __name__ == "__main__":
    app.run_server(debug=True)
