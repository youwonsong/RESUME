package com.example.petmash;

import android.content.Intent;
import android.os.Bundle;
import android.widget.Button;
import androidx.appcompat.app.AppCompatActivity;

public class ProfileActivity extends AppCompatActivity {

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_profile);

        Button btnGoToUpload = findViewById(R.id.btnGoToUpload);

        btnGoToUpload.setOnClickListener(v -> {
            Intent intent = new Intent(ProfileActivity.this, UploadPhotoActivity.class);
            startActivity(intent);
        });
    }
}