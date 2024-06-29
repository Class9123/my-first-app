from flask import Flask, render_template_string
from flask_socketio import SocketIO, emit

app = Flask(__name__)
socketio = SocketIO(app)

@app.route('/')
def index():
    html_code = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Simple Video Call</title>
    </head>
    <body>
        <h1>Simple Video Call</h1>
        <video id="localVideo" autoplay muted></video>
        <video id="remoteVideo" autoplay></video>
        <script src="https://cdn.socket.io/4.0.0/socket.io.min.js"></script>
        <script>
            const socket = io();
            let localStream;
            let remoteStream;
            let peerConnection;

            const localVideo = document.getElementById('localVideo');
            const remoteVideo = document.getElementById('remoteVideo');

            const constraints = {
                video: true,
                audio: true
            };

            async function startCall() {
                try {
                    localStream = await navigator.mediaDevices.getUserMedia(constraints);
                    localVideo.srcObject = localStream;

                    const configuration = {
                        iceServers: [{ urls: 'stun:stun.l.google.com:19302' }]
                    };

                    peerConnection = new RTCPeerConnection(configuration);

                    localStream.getTracks().forEach(track => peerConnection.addTrack(track, localStream));

                    peerConnection.onicecandidate = event => {
                        if (event.candidate) {
                            socket.emit('candidate', event.candidate);
                        }
                    };

                    peerConnection.ontrack = event => {
                        remoteStream = event.streams[0];
                        remoteVideo.srcObject = remoteStream;
                    };

                    const offer = await peerConnection.createOffer();
                    await peerConnection.setLocalDescription(offer);
                    socket.emit('offer', offer);
                } catch (error) {
                    console.error('Error accessing media devices.', error);
                }
            }

            socket.on('offer', async (offer) => {
                if (!peerConnection) {
                    startCall();
                }
                await peerConnection.setRemoteDescription(new RTCSessionDescription(offer));
                const answer = await peerConnection.createAnswer();
                await peerConnection.setLocalDescription(answer);
                socket.emit('answer', answer);
            });

            socket.on('answer', async (answer) => {
                await peerConnection.setRemoteDescription(new RTCSessionDescription(answer));
            });

            socket.on('candidate', async (candidate) => {
                await peerConnection.addIceCandidate(new RTCIceCandidate(candidate));
            });

            startCall();
        </script>
    </body>
    </html>
    """
    return render_template_string(html_code)

@socketio.on('offer')
def handle_offer(data):
    emit('offer', data, broadcast=True)

@socketio.on('answer')
def handle_answer(data):
    emit('answer', data, broadcast=True)

@socketio.on('candidate')
def handle_candidate(data):
    emit('candidate', data, broadcast=True)

if __name__ == '__main__':
    socketio.run(app, debug=True)
