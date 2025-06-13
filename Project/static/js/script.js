const { useState, useEffect } = React;

const API_BASE_URL = "http://localhost:8000/api";

function saveTokens(accessToken, refreshToken) {
    localStorage.setItem('accessToken', accessToken);
    localStorage.setItem('refreshToken', refreshToken);
}

function loadTokens() {
    return {
        accessToken: localStorage.getItem('accessToken'),
        refreshToken: localStorage.getItem('refreshToken'),
    };
}

function removeTokens() {
    localStorage.removeItem('accessToken');
    localStorage.removeItem('refreshToken');
}

async function apiRequest(path, method = 'GET', body = null, token = null) {
    const headers = {};
    if (token) headers['Authorization'] = 'Bearer ' + token;
    if (body && !(body instanceof FormData)) {
        headers['Content-Type'] = 'application/json';
        body = JSON.stringify(body);
    }
    try {
        const res = await fetch(API_BASE_URL + path, {
            method,
            headers,
            body,
        });
        const data = await res.json();
        if (!res.ok) {
            console.error("API error response:", data);
            throw new Error(data.detail || 'API error');
        }
        return data;
    } catch (e) {
        throw e;
    }
}

function AuthForm({ onLogin, onRegister, isLoginMode, toggleMode, error }) {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [loading, setLoading] = useState(false);
    const handleSubmit = async e => {
        e.preventDefault();
        setLoading(true);
        try {
            if (isLoginMode) {
                await onLogin(username, password);
            } else {
                await onRegister(username, password);
            }
            setUsername('');
            setPassword('');
        } catch (e) {
            // error handled by parent
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="auth-section" role="region" aria-label={isLoginMode ? "Login form" : "Register form"}>
            <h2>{isLoginMode ? 'Login' : 'Register'}</h2>
            {error && <div className="error-message" role="alert">{error}</div>}
            <form onSubmit={handleSubmit}>
                <label htmlFor="username-input">Username</label>
                <input
                    type="text"
                    id="username-input"
                    value={username}
                    onChange={e => setUsername(e.target.value)}
                    required
                    minLength={3}
                    maxLength={30}
                    autoComplete="username"
                />
                <label htmlFor="password-input">Password</label>
                <input
                    type="password"
                    id="password-input"
                    value={password}
                    onChange={e => setPassword(e.target.value)}
                    required
                    minLength={6}
                    maxLength={100}
                    autoComplete={isLoginMode ? "current-password" : "new-password"}
                />
                <button type="submit" disabled={loading}>{loading ? (isLoginMode ? 'Logging in...' : 'Registering...') : (isLoginMode ? 'Login' : 'Register')}</button>
            </form>
            <button className="auth-toggle" onClick={toggleMode} aria-label="Switch authentication mode">
                {isLoginMode ? 'Need to register? Click here' : 'Already have an account? Login here'}
            </button>
        </div>
    );
}

function App() {
    const [darkMode, setDarkMode] = useState(false);
    const [tokens, setTokens] = useState(loadTokens());
    const [token, setToken] = useState(tokens.accessToken);
    const [authError, setAuthError] = useState(null);
    const [uploadFile, setUploadFile] = useState(null);
    const [summary, setSummary] = useState('');
    const [uploading, setUploading] = useState(false);
    const [summaryError, setSummaryError] = useState(null);
    const [loadingHistory, setLoadingHistory] = useState(false);
    const [history, setHistory] = useState([]);
    const [selectedSummary, setSelectedSummary] = useState(null);
    const [isLoginMode, setIsLoginMode] = useState(true);

    useEffect(() => {
        document.body.classList.toggle('dark', darkMode);
    }, [darkMode]);

    useEffect(() => {
        if (tokens.accessToken) {
            saveTokens(tokens.accessToken, tokens.refreshToken);
            setToken(tokens.accessToken);
        } else {
            removeTokens();
            setToken(null);
        }
    }, [tokens]);

    useEffect(() => {
        if (token) {
            fetchHistory();
        } else {
            setHistory([]);
            setSelectedSummary(null);
            setSummary('');
        }
    }, [token]);

    async function fetchHistory() {
        setLoadingHistory(true);
        setSummaryError(null);
        try {
            const data = await apiRequest('/summaries/', 'GET', null, token);
            setHistory(data || []);
        } catch (e) {
            setSummaryError("Failed to load history: " + e.message);
        } finally {
            setLoadingHistory(false);
        }
    }

    async function handleLogin(username, password) {
        setAuthError(null);
        const payload = { username, password };
        try {
            const data = await apiRequest('/auth/login/', 'POST', payload);
            // Expect data to include access and refresh tokens
            if (data.access && data.refresh) {
                setTokens({ accessToken: data.access, refreshToken: data.refresh });
            } else {
                throw new Error('Invalid login response tokens');
            }
        } catch (e) {
            setAuthError(e.message);
            throw e;
        }
    }

    async function handleRegister(username, password) {
        setAuthError(null);
        try {
            const data = await apiRequest('/auth/register/', 'POST', { username, password });
            // For registration, tokens are 'access' and 'refresh' to be consistent with login
            if (data.access && data.refresh) {
                setTokens({ accessToken: data.access, refreshToken: data.refresh });
            } else {
                throw new Error('Invalid register response tokens');
            }
        } catch (e) {
            setAuthError(e.message);
            throw e;
        }
    }

    function logout() {
        setTokens({ accessToken: null, refreshToken: null });
        setSummary('');
        setUploadFile(null);
        setSelectedSummary(null);
    }

    function resetSummary() {
        setSummary('');
        setSelectedSummary(null);
    }

    async function handleFileUpload(e) {
        setSummaryError(null);
        const file = e.target.files[0];
        if (file && file.type !== 'application/pdf') {
            setSummaryError("Please upload a valid PDF file");
            e.target.value = null;
            return;
        }
        setUploadFile(file);
        resetSummary();
    }

    async function submitFile() {
        if (!uploadFile) return;
        setUploading(true);
        setSummaryError(null);
        setSummary('');
        setSelectedSummary(null);
        try {
            const formData = new FormData();
            formData.append('file', uploadFile);

            const res = await fetch(API_BASE_URL + '/summarize/', {
                method: 'POST',
                headers: {
                    'Authorization': 'Bearer ' + token,
                },
                body: formData,
            });
            if (!res.ok) {
                const errData = await res.json();
                throw new Error(errData.detail || 'Failed to summarize the file');
            }
            const data = await res.json();
            setSummary(data.summary);
            fetchHistory();
        } catch (e) {
            setSummaryError("Error: " + e.message);
        } finally {
            setUploading(false);
        }
    }

    function downloadSummary() {
        if (!summary) return;
        const element = document.createElement('a');
        const file = new Blob([summary], { type: 'text/plain' });
        element.href = URL.createObjectURL(file);
        element.download = 'summary.txt';
        document.body.appendChild(element);
        element.click();
        document.body.removeChild(element);
    }

    async function loadHistorySummary(id) {
        setSummaryError(null);
        setUploading(true);
        try {
            const data = await apiRequest(`/summaries/${id}/`, 'GET', null, token);
            setSummary(data.summary);
            setSelectedSummary(id);
        } catch (e) {
            setSummaryError("Failed to load summary: " + e.message);
        } finally {
            setUploading(false);
        }
    }

    return (
        <>
            <header>
                <h1>AI-Powered Notes Summarizer</h1>
                <button
                    className="dark-mode-toggle"
                    onClick={() => setDarkMode(!darkMode)}
                    aria-pressed={darkMode}
                    aria-label={darkMode ? 'Switch to light mode' : 'Switch to dark mode'}
                >
                    {darkMode ? 'Light Mode' : 'Dark Mode'}
                </button>  
            </header>

            {!token ? (
                <AuthForm
                    isLoginMode={isLoginMode}
                    toggleMode={() => {
                        setAuthError(null);
                        setIsLoginMode(!isLoginMode);   
                    }}
                    onLogin={handleLogin}
                    onRegister={handleRegister}
                    error={authError}
                />
            ) : (
            <>
                <section aria-label="File upload for notes summarization">
                    <form onSubmit={e => { e.preventDefault(); submitFile(); }}>
                        <label htmlFor="file-upload">Upload PDF Notes</label>
                        <input
                            type="file"
                            id="file-upload"
                            accept="application/pdf"
                            onChange={handleFileUpload}
                            disabled={uploading}
                            aria-describedby="file-help"
                        />
                        <small id="file-help">Choose a PDF file to get a summary</small>
                        <button type="submit" disabled={!uploadFile || uploading}>
                            {uploading ? 'Summarizing...' : 'Summarize'}
                        </button>
                    </form>
                    {summaryError && <p className="error-message" role="alert">{summaryError}</p>}
                </section>

                <section aria-label="Summary result" className="summary-area" tabIndex="0" role="region" aria-live="polite">
                    {summary ? (
                        <>
                            <h2>Summary</h2>
                            <p>{summary}</p>
                            <button className="download-button" onClick={downloadSummary} aria-label="Download summary as text file">
                                Download Summary
                            </button>
                        </>
                    ) : (
                        <p>No summary generated yet.</p>
                    )}
                </section>

                <section className="history-section" aria-label="Summary history">
                    <h2 className="history-title">Summary History</h2>
                    {loadingHistory ? (
                        <p>Loading history...</p>
                    ) : history.length === 0 ? (
                        <p>No past summaries found.</p>
                    ) : (
                        <ul className="history-list" tabIndex="0">
                            {history.map(({ id, filename, created_at }) => (
                                <li
                                    key={id}
                                    className="history-item"
                                    tabIndex="0"
                                    role="button"
                                    aria-pressed={selectedSummary === id}
                                    onClick={() => loadHistorySummary(id)}
                                    onKeyDown={e => {
                                        if (e.key === 'Enter' || e.key === ' ') {
                                            e.preventDefault();
                                            loadHistorySummary(id);
                                        }
                                    }}
                                    title={`View summary for ${filename} uploaded on ${new Date(created_at).toLocaleString()}`}
                                >
                                    {filename} - {new Date(created_at).toLocaleString()}
                                </li>
                            ))}
                        </ul>
                    )}
                </section>

                <button onClick={logout} aria-label="Logout of the application" className="logout-button">
                    Logout
                </button>
            </>
            )}

            <footer>
                &copy; {new Date().getFullYear()} AI-Powered Notes Summarizer. Powered by OpenAI.
            </footer>
        </>
    );
}

ReactDOM.createRoot(document.getElementById('root')).render(<App />);

