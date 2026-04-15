package io.greenthumb.auth.controller;

import io.greenthumb.auth.service.AuthService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

/**
 * Auth REST controller.
 *
 * <p>Exposes the three endpoints consumed by the rest of the system:
 * <ul>
 *   <li>{@code POST /auth/login}    — returns a signed JWT for valid credentials</li>
 *   <li>{@code GET  /auth/validate} — validates a JWT (called by greenthumb-api)</li>
 * </ul>
 */
@RestController
@RequestMapping("/auth")
@RequiredArgsConstructor
public class AuthController {

    private final AuthService authService;

    /**
     * Login endpoint.
     *
     * @param body JSON with {@code email} and {@code password} keys.
     * @return 200 with {@code {"token": "..."}} or 401 on bad credentials.
     */
    @PostMapping("/login")
    public ResponseEntity<Map<String, String>> login(@RequestBody Map<String, String> body) {
        String token = authService.login(body.get("email"), body.get("password"));
        return ResponseEntity.ok(Map.of("token", token));
    }

    /**
     * Token validation endpoint — called service-to-service by greenthumb-api.
     *
     * <p>The greenthumb-api Python dependency {@code get_current_user_id} hits
     * this endpoint on every admin request.
     *
     * @param authHeader {@code Authorization: Bearer <token>}
     * @return 200 with {@code {"id_user": "<uuid>"}} or 401.
     */
    @GetMapping("/validate")
    public ResponseEntity<Map<String, String>> validate(
            @RequestHeader("Authorization") String authHeader) {
        String token = authHeader.replace("Bearer ", "");
        String userId = authService.validateAndGetUserId(token);
        return ResponseEntity.ok(Map.of("id_user", userId));
    }
}
