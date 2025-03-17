from flask import Flask, request, render_template_string
import socket

app = Flask(__name__)

def send_udp_command(message, host='127.0.0.1', port=9999):
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_socket:
        udp_socket.sendto(message.encode('utf-8'), (host, port))
        print(f"Sent command: {message}")

html_page = """
<!doctype html>
<html>
  <head>
    <title>UDP Command Slider</title>
    <script>
      function sendSliderValue(val) {
        fetch('/set_target', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({target: val})
        })
        .then(response => response.text())
        .then(data => console.log(data))
        .catch(error => console.error(error));
      }
    </script>
  </head>
  <body>
    <h1>UDP Command Slider</h1>
    <!-- Slider from 0.0 to 1.5 -->
    <input type="range" min="0.0" max="1.5" step="0.01" value="0.0" 
           oninput="document.getElementById('value').innerText=this.value; sendSliderValue(this.value)">
    <p>Value: <span id="value">0.0</span></p>
  </body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(html_page)

@app.route("/set_target", methods=["POST"])
def set_target():
    data = request.get_json()
    if not data or "target" not in data:
        return "Missing target value", 400
    message = f"axis:2:{data['target']}"
    send_udp_command(message)
    return f"Command sent: {message}"

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)
