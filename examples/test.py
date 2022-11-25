from httpfast import HttpFast


# Starts a client where you can send HTTP/s requests
# Connections will open at the first request per HOST
client = HttpFast()

# Sends a GET request using SSL
response = client.get("https://httpbin.org/get")
print(response.text) #string

# Sends a POST request using HTTP with no SSL with the payload credits: github.com/phishontop
response = client.post("http://httpbin.org/post", data={"credits": "github.com/phishontop"})
print(response.json()) #dict
