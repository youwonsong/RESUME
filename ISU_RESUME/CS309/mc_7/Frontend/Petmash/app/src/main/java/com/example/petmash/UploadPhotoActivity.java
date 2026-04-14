package com.example.petmash;

import android.content.Intent;
import android.net.Uri;
import android.os.Bundle;
import android.util.Log;
import android.widget.Button;
import android.widget.ImageView;
import android.widget.Toast;
import androidx.appcompat.app.AppCompatActivity;

import java.io.File;
import java.io.FileOutputStream;
import java.io.InputStream;

import okhttp3.MediaType;
import okhttp3.MultipartBody;
import okhttp3.RequestBody;
import retrofit2.Call;
import retrofit2.Callback;
import retrofit2.Response;
import retrofit2.Retrofit;
import retrofit2.converter.gson.GsonConverterFactory;

public class UploadPhotoActivity extends AppCompatActivity {

    private static final int PICK_IMAGE_REQUEST = 1;
    private ImageView ivPreview;
    private Uri selectedImageUri;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_upload_photo);

        ivPreview = findViewById(R.id.ivPreview);
        Button btnSelectPhoto = findViewById(R.id.btnSelectPhoto);
        Button btnUpload = findViewById(R.id.btnUpload);


        btnSelectPhoto.setOnClickListener(v -> {
            Intent intent = new Intent(Intent.ACTION_PICK);
            intent.setType("image/*");
            startActivityForResult(intent, PICK_IMAGE_REQUEST);
        });


        btnUpload.setOnClickListener(v -> {
            if (selectedImageUri != null) {

                File file = getFileFromUri(selectedImageUri);
                if (file != null) {

                    sendImageToServer(file, "MyPet");
                }
            } else {
                Toast.makeText(this, "먼저 사진을 선택해주세요!", Toast.LENGTH_SHORT).show();
            }
        });
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);

        if (requestCode == PICK_IMAGE_REQUEST && resultCode == RESULT_OK && data != null && data.getData() != null) {
            selectedImageUri = data.getData();
            ivPreview.setImageURI(selectedImageUri);
        }
    }

    private void sendImageToServer(File file, String petName) {
        Retrofit retrofit = new Retrofit.Builder()

                //.baseUrl(BuildConfig.SERVER_URL)
                .addConverterFactory(GsonConverterFactory.create())
                .build();

        PetService service = retrofit.create(PetService.class);

        RequestBody requestFile = RequestBody.create(MediaType.parse("image/*"), file);
        MultipartBody.Part body = MultipartBody.Part.createFormData("file", file.getName(), requestFile);

        RequestBody name = RequestBody.create(MediaType.parse("text/plain"), petName);

        service.uploadPet(body, name).enqueue(new Callback<String>() {
            @Override
            public void onResponse(Call<String> call, Response<String> response) {
                if (response.isSuccessful()) {
                    Toast.makeText(UploadPhotoActivity.this, "서버 전송 성공! 맥 폴더를 확인하세요.", Toast.LENGTH_LONG).show();
                    Log.d("Retrofit", "Success: " + response.body());
                } else {
                    Toast.makeText(UploadPhotoActivity.this, "서버 응답 에러", Toast.LENGTH_SHORT).show();
                }
            }

            @Override
            public void onFailure(Call<String> call, Throwable t) {
                Toast.makeText(UploadPhotoActivity.this, "연결 실패: " + t.getMessage(), Toast.LENGTH_LONG).show();
                Log.e("Retrofit", "Error: ", t);
            }
        });
    }

    private File getFileFromUri(Uri uri) {
        try {
            InputStream inputStream = getContentResolver().openInputStream(uri);
            File tempFile = new File(getCacheDir(), "temp_image.jpg");
            FileOutputStream outputStream = new FileOutputStream(tempFile);

            byte[] buffer = new byte[1024];
            int read;
            while ((read = inputStream.read(buffer)) != -1) {
                outputStream.write(buffer, 0, read);
            }
            outputStream.flush();
            return tempFile;
        } catch (Exception e) {
            e.printStackTrace();
            return null;
        }
    }
}