package com.example.petmash;

import android.os.Bundle;
import android.widget.Button;
import android.widget.EditText;
import android.widget.Toast;
import androidx.appcompat.app.AppCompatActivity;
import com.android.volley.Request;
import com.android.volley.toolbox.JsonObjectRequest;
import com.android.volley.toolbox.Volley;
import org.json.JSONException;
import org.json.JSONObject;

public class SignUpActivity extends AppCompatActivity {
    private EditText etFullName, etEmail, etUsername, etPassword;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_signup);

        etFullName = findViewById(R.id.etFullName);
        etEmail = findViewById(R.id.etEmail);
        etUsername = findViewById(R.id.etUsername);
        etPassword = findViewById(R.id.etPassword);
        Button btnRegister = findViewById(R.id.btnRegister);

        btnRegister.setOnClickListener(v -> registerUser());
    }

    private void registerUser() {
        String name = etFullName.getText().toString();
        String email = etEmail.getText().toString();
        String user = etUsername.getText().toString();
        String pass = etPassword.getText().toString();


        if (!Validation.isValidEmail(email)) { Toast.makeText(this, "Invalid Email", Toast.LENGTH_SHORT).show(); return; }
        if (Validation.isEmpty(user)) { Toast.makeText(this, "Username is required", Toast.LENGTH_SHORT).show(); return; }
        if (!Validation.isValidPassword(pass)) { Toast.makeText(this, "Password too short", Toast.LENGTH_SHORT).show(); return; }


        String url = "http://10.0.2.2:8080/signup";
        JSONObject body = new JSONObject();
        try {
            body.put("name", name); body.put("email", email);
            body.put("user_name", user); body.put("password", pass);
        } catch (JSONException e) { e.printStackTrace(); }

        JsonObjectRequest request = new JsonObjectRequest(Request.Method.POST, url, body,
                response -> {
                    try {
                        if (response.getBoolean("success")) {
                            Toast.makeText(this, "Registration Success!", Toast.LENGTH_SHORT).show();
                            finish();
                        } else {
                            Toast.makeText(this, response.getString("message"), Toast.LENGTH_LONG).show();
                        }
                    } catch (JSONException e) { e.printStackTrace(); }
                },
                error -> Toast.makeText(this, "Server Error or Duplicate Entry", Toast.LENGTH_SHORT).show()
        );
        Volley.newRequestQueue(this).add(request);
    }
}