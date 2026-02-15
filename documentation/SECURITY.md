# Security Policy

## Supported Versions

Currently supported versions for security updates:

| Version | Supported          |
| ------- | ------------------ |
| 2.0.x   | :white_check_mark: |
| < 2.0   | :x:                |

## Reporting a Vulnerability

**Please DO NOT report security vulnerabilities through public GitHub issues.**

### How to Report

If you discover a security vulnerability, please email:

📧 **sefy76@gmail.com**

**Subject line:** `[SECURITY] Brief description`

### What to Include

Please provide:

1. **Type of vulnerability** (e.g., data exposure, code injection, authentication bypass)
2. **Location** (file, function, line number if known)
3. **Steps to reproduce** the issue
4. **Potential impact** of the vulnerability
5. **Suggested fix** (if you have one)
6. **Your contact information** for follow-up questions

### Example Report

```
Subject: [SECURITY] Potential SQL injection in data import

Type: SQL Injection
Location: plugins/database_connector.py, line 145
Impact: Could allow arbitrary database queries

Steps to reproduce:
1. Import data from external database
2. Use crafted input: '; DROP TABLE samples; --
3. Query executes unintended command

Suggested fix: Use parameterized queries instead of string concatenation

Contact: your-email@example.com
```

## Response Timeline

- **Acknowledgment**: Within 48 hours of report
- **Initial Assessment**: Within 7 days
- **Fix Development**: Varies by severity
- **Public Disclosure**: After fix is released

## Security Best Practices for Users

### API Keys

**NEVER commit API keys to version control!**

✅ **Correct:**
```bash
# Set as environment variable
export OPENAI_API_KEY="sk-..."

# Or use .env file (add to .gitignore)
echo "OPENAI_API_KEY=sk-..." > .env
```

❌ **Incorrect:**
```python
# Don't hardcode keys!
api_key = "sk-abc123..."  # Bad!
```

### Data Privacy

**Sensitive Data:**
- DO NOT share data containing personal information
- DO NOT upload proprietary research data to public repos
- DO NOT send sensitive data to AI assistants without reviewing first

**Recommendations:**
1. Use anonymized sample IDs
2. Remove location data if not needed
3. Filter columns before exporting
4. Check file permissions

### Secure Configuration

**Protect your config files:**
```bash
# Set restrictive permissions
chmod 600 config/api_keys.json
chmod 700 config/

# Keep configs out of version control
echo "config/*_secret.json" >> .gitignore
```

### Updates

**Stay Updated:**
- Watch repository for security announcements
- Update regularly: `git pull && pip install -r requirements.txt --upgrade`
- Subscribe to security advisories

## Known Security Considerations

### 1. AI Integrations

**Risk**: Data sent to AI providers may be stored/logged

**Mitigation**:
- Only use AI features with non-sensitive data
- Review AI provider's privacy policy
- Consider local models (Ollama) for sensitive work
- Can disable AI plugins entirely

### 2. Hardware Connections

**Risk**: Malicious firmware could send false data

**Mitigation**:
- Only connect trusted instruments
- Verify instrument firmware
- Use read-only connections when possible

### 3. File Imports

**Risk**: Malicious CSV/Excel files could contain harmful macros

**Mitigation**:
- Toolkit doesn't execute macros
- Validates data types during import
- Sanitizes column names

### 4. Plugin System

**Risk**: Third-party plugins could contain malicious code

**Mitigation**:
- Only install plugins from trusted sources
- Review plugin code before enabling
- Plugins run with same permissions as main app
- Consider sandboxing for untrusted plugins

### 5. Web Connections

**Risk**: Man-in-the-middle attacks on API calls

**Mitigation**:
- All API calls use HTTPS
- Certificate validation enabled
- Use secure networks for sensitive work

## Vulnerability Disclosure Policy

### Our Commitment

We are committed to:
- Responding to security reports promptly
- Keeping reporters informed of progress
- Crediting reporters (unless they prefer anonymity)
- Releasing fixes in a timely manner

### Coordinated Disclosure

For serious vulnerabilities, we follow coordinated disclosure:

1. **Private reporting** to maintainers
2. **Fix development** in private
3. **Security advisory** created (GitHub)
4. **Fix released** in new version
5. **Public disclosure** after users have time to update
6. **Credit given** to reporter (if desired)

### Embargo Period

We request a **14-day embargo** before public disclosure to allow time for:
- Fix development
- Testing
- User notification
- Coordinated release

## Scope

### In Scope

Security issues in:
- Main toolkit codebase
- Official plugins (in this repository)
- Build and distribution process
- Documentation with security implications

### Out of Scope

- Third-party dependencies (report to those projects)
- User-created custom plugins
- Issues requiring physical access to user's computer
- Social engineering attacks
- Outdated/unsupported versions

## Recognition

We appreciate security researchers and will:

- Credit you in the security advisory (unless you prefer anonymity)
- Mention you in CHANGELOG.md
- Thank you publicly (with permission)

**Hall of Fame**: (Will list security reporters here)
- [Be the first!]

## Security Contacts

**Primary**: sefy76@gmail.com

**Response Times**:
- Critical: 24-48 hours
- High: 3-7 days
- Medium: 7-14 days
- Low: 14-30 days

## Past Security Advisories

None yet - this is the first public release.

Future advisories will be listed here with:
- CVE number (if applicable)
- Severity rating
- Affected versions
- Fixed in version
- Brief description

## Compliance

This project is for research and educational use. We do not claim compliance with:
- HIPAA (healthcare)
- GDPR (though we respect privacy)
- SOC 2 (no formal audit)
- ISO 27001 (not certified)

If you need certified software, please contact us about commercial licensing.

## Questions?

For security questions that don't involve specific vulnerabilities:
- Open a GitHub Discussion
- Email: sefy76@gmail.com
- See FAQ in documentation

---

**Thank you for helping keep Scientific Toolkit secure!** 🔒

*Last Updated: February 2026*
