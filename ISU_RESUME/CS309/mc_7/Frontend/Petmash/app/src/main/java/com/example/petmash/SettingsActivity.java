package com.example.petmash;


import android.content.Intent;
import android.os.Bundle;
import android.widget.Button;
import androidx.appcompat.app.AppCompatActivity;

public class SettingsActivity extends AppCompatActivity {
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_settings);

        Button btnLikeHistory = findViewById(R.id.btnLikeHistory);
        btnLikeHistory.setOnClickListener(v -> {

        });

        Button btnModerator = findViewById(R.id.btnModerator);
        btnModerator.setOnClickListener(v -> {

        });
    }
}