package com.example.petmash;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;
import java.io.File;
import java.io.IOException;
import java.util.UUID;

@RestController
@RequestMapping("/api")
public class PetController {

    @Autowired
    private JdbcTemplate jdbcTemplate;

    @Value("${file.upload-dir}")
    private String uploadDir;

    @PostMapping("/upload")
    public String uploadPet(@RequestParam("file") MultipartFile file,
                            @RequestParam("name") String name) {
        try {
            File dir = new File(uploadDir);
            if (!dir.exists()) dir.mkdirs();
            String fileName = UUID.randomUUID() + "_" + file.getOriginalFilename();
            File dest = new File(uploadDir + fileName);
            file.transferTo(dest);
            String sql = "INSERT INTO PET (pet_name, owner_id, image_path) VALUES (?, 1, ?)";
            jdbcTemplate.update(sql, name, fileName);

            return "Success! File name: " + fileName;
        } catch (IOException e) {
            return "Failed: " + e.getMessage();
        }
    }
}