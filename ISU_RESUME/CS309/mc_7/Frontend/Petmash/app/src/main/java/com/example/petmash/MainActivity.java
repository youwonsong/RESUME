package com.example.petmash;

import android.os.Bundle;
import android.widget.Button;
import android.widget.ImageView;
import android.widget.TextView;
import android.widget.Toast;
import androidx.appcompat.app.AppCompatActivity;
import com.android.volley.Request;
import com.android.volley.toolbox.JsonObjectRequest;
import com.android.volley.toolbox.Volley;
import org.java_websocket.client.WebSocketClient;
import org.java_websocket.handshake.ServerHandshake;
import org.json.JSONException;
import org.json.JSONObject;
import java.net.URI;
import java.net.URISyntaxException;

public class MainActivity extends AppCompatActivity {
    private WebSocketClient webSocketClient;
    private TextView tvChatLog;
    private ImageView ivPet1, ivPet2;
    private int currentUserId;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        currentUserId = getIntent().getIntExtra("user_id", -1);

        tvChatLog = findViewById(R.id.tvChatLog);
        ivPet1 = findViewById(R.id.ivPet1);
        ivPet2 = findViewById(R.id.ivPet2);
        Button btnVotePet1 = findViewById(R.id.btnVotePet1);
        Button btnVotePet2 = findViewById(R.id.btnVotePet2);

        connectWebSocket();
        loadNextPair(); // 대결할 반려동물 불러오기

        btnVotePet1.setOnClickListener(v -> voteForPet(101));
        btnVotePet2.setOnClickListener(v -> voteForPet(102));
    }

    private void connectWebSocket() {
        URI uri;
        try {
            uri = new URI("ws://10.0.2.2:8080/chat/" + currentUserId);
        } catch (URISyntaxException e) { return; }

        webSocketClient = new WebSocketClient(uri) {
            @Override
            public void onOpen(ServerHandshake handshakedata) { }

            @Override
            public void onMessage(String message) {
                runOnUiThread(() -> {

                    tvChatLog.append("\n" + message);
                });
            }

            @Override
            public void onClose(int code, String reason, boolean remote) { }

            @Override
            public void onError(Exception ex) { }
        };
        webSocketClient.connect();
    }

    private void voteForPet(int petId) {

        String url = "http://api.petmash.com/vote/" + petId;
        JsonObjectRequest request = new JsonObjectRequest(Request.Method.POST, url, null,
                response -> {
                    Toast.makeText(this, "Vote Casted!", Toast.LENGTH_SHORT).show();
                    loadNextPair();
                }, error -> { /* 에러 처리 */ });
        Volley.newRequestQueue(this).add(request);
    }

    private void loadNextPair() {
    }
}