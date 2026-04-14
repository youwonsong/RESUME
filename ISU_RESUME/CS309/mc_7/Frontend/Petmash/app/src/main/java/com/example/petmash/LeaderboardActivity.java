package com.example.petmash;

import android.os.Bundle;
import android.widget.Toast;
import androidx.appcompat.app.AppCompatActivity;
import androidx.recyclerview.widget.LinearLayoutManager;
import androidx.recyclerview.widget.RecyclerView;
import com.android.volley.Request;
import com.android.volley.RequestQueue;
import com.android.volley.toolbox.JsonArrayRequest;
import com.android.volley.toolbox.Volley;
import org.json.JSONException;
import org.json.JSONObject;
import java.util.ArrayList;
import java.util.List;

public class LeaderboardActivity extends AppCompatActivity {
    private RecyclerView rvLeaderboard;
    private LeaderboardAdapter adapter;
    private List<Pet> petList;
    private RequestQueue requestQueue;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_leaderboard);

        rvLeaderboard = findViewById(R.id.rvLeaderboard);
        rvLeaderboard.setLayoutManager(new LinearLayoutManager(this));

        petList = new ArrayList<>();
        requestQueue = Volley.newRequestQueue(this);

        loadLeaderboardData();
    }

    private void loadLeaderboardData() {
        String url = "http://10.0.2.2:8080/leaderboard";

        JsonArrayRequest request = new JsonArrayRequest(Request.Method.GET, url, null,
                response -> {
                    petList.clear();
                    for (int i = 0; i < response.length(); i++) {
                        try {
                            JSONObject obj = response.getJSONObject(i);
                            Pet pet = new Pet();
                            pet.setName(obj.getString("pet_name"));
                            pet.setScore(obj.getInt("score"));
                            petList.add(pet);
                        } catch (JSONException e) {
                            e.printStackTrace();
                        }
                    }
                    adapter = new LeaderboardAdapter(petList);
                    rvLeaderboard.setAdapter(adapter);
                },
                error -> Toast.makeText(LeaderboardActivity.this, "리더보드 로딩 실패", Toast.LENGTH_SHORT).show()
        );
        requestQueue.add(request);
    }
}