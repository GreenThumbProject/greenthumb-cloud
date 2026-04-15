package io.greenthumb.auth.service;

import io.greenthumb.auth.model.AppUser;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.security.Keys;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.stereotype.Service;

import jakarta.persistence.EntityManager;
import jakarta.persistence.NoResultException;
import jakarta.persistence.PersistenceContext;
import javax.crypto.SecretKey;
import java.nio.charset.StandardCharsets;
import java.util.Date;

/**
 * Business logic for login and JWT validation.
 *
 * <p>Adaptation notes (from hbrn-fastapi-template):
 * <ul>
 *   <li>JWT subject is {@code id_user} UUID string (not an integer user ID)</li>
 *   <li>Expiry: 24 hours by default (configurable via {@code jwt.expiry-ms})</li>
 * </ul>
 */
@Service
public class AuthService {

    @Value("${jwt.secret}")
    private String jwtSecret;

    @Value("${jwt.expiry-ms:86400000}")
    private long jwtExpiryMs;

    @PersistenceContext
    private EntityManager em;

    private final BCryptPasswordEncoder encoder = new BCryptPasswordEncoder();

    /**
     * Authenticate and return a signed JWT.
     *
     * @throws org.springframework.security.authentication.BadCredentialsException
     *         if email not found or password doesn't match.
     */
    public String login(String email, String password) {
        AppUser user = findByEmail(email);
        if (!encoder.matches(password, user.getPasswordHash())) {
            throw new org.springframework.security.authentication
                    .BadCredentialsException("Invalid credentials");
        }
        return buildJwt(user.getIdUser().toString());
    }

    /**
     * Validate a JWT and return the {@code id_user} UUID string.
     *
     * @throws io.jsonwebtoken.JwtException if the token is invalid or expired.
     */
    public String validateAndGetUserId(String token) {
        return Jwts.parser()
                .verifyWith(signingKey())
                .build()
                .parseSignedClaims(token)
                .getPayload()
                .getSubject();
    }

    // ------------------------------------------------------------------

    private String buildJwt(String subject) {
        return Jwts.builder()
                .subject(subject)
                .issuedAt(new Date())
                .expiration(new Date(System.currentTimeMillis() + jwtExpiryMs))
                .signWith(signingKey())
                .compact();
    }

    private SecretKey signingKey() {
        return Keys.hmacShaKeyFor(jwtSecret.getBytes(StandardCharsets.UTF_8));
    }

    private AppUser findByEmail(String email) {
        try {
            return em.createQuery(
                    "SELECT u FROM AppUser u WHERE u.email = :email", AppUser.class)
                    .setParameter("email", email)
                    .getSingleResult();
        } catch (NoResultException e) {
            throw new org.springframework.security.authentication
                    .BadCredentialsException("Invalid credentials");
        }
    }
}
