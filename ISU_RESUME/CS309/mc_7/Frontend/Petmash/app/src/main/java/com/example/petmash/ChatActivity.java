package com.example.petmash;

import android.os.Bundle;
import android.widget.Button;
import android.widget.EditText;
import android.widget.TextView;
import androidx.appcompat.app.AppCompatActivity;

import java.net.URI;
import java.net.URISyntaxException;

public class ChatActivity extends AppCompatActivity {
    private WebSocketClient mWebSocketClient;
    private TextView tvChatLog;
    private EditText etChatInput;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_chat);

        tvChatLog = findViewById(R.id.tvChatLog);
        etChatInput = findViewById(R.id.etChatInput);
        Button btnSend = findViewById(R.id.btnSend);

        connectWebSocket();

        btnSend.setOnClickListener(v -> {
            String message = etChatInput.getText().toString();
            if (mWebSocketClient != null && mWebSocketClient.isOpen() && !message.isEmpty()) {
                mWebSocketClient.send(message);
                etChatInput.setText("");
            }
        });
    }

    private void connectWebSocket() {
        URI uri;
        try {
            uri = new URI("ws://10.0.2.2:8080/chat/user" + System.currentTimeMillis());
        } catch (URISyntaxException e) {
            e.printStackTrace();
            return;
        }

        mWebSocketClient = new WebSocketClient(uri) {
            @Override
            public void onOpen(ServerHandshake serverHandshake) {
                runOnUiThread(() -> tvChatLog.append("\n[System] Connected to server"));
            }

            @Override
            public void onMessage(String s) {
                runOnUiThread(() -> tvChatLog.append("\n" + s));
            }

            @Override
            public void onClose(int i, String s, boolean b) {
                runOnUiThread(() -> tvChatLog.append("\n[System] Connection closed"));
            }

            @Override
            public void onError(Exception e) {
                runOnUiThread(() -> tvChatLog.append("\n[Error] " + e.getMessage()));
            }

            @Override
            public void onStart() {
            }
        };
        mWebSocketClient.connect();
    }
}