import { useState } from 'react';
import SourceSnippet from './SourceSnippet';
import './QueryInterface.css';

function QueryInterface() {
    const [question, setQuestion] = useState('');
    const [answer, setAnswer] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        setAnswer(null);
        setLoading(true);

        try {
            const { queryKnowledgeBase } = await import('../services/api');
            const result = await queryKnowledgeBase(question);
            setAnswer(result);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="query-interface">
            <h2>Ask a Question</h2>

            <form onSubmit={handleSubmit}>
                <div className="question-input-wrapper">
                    <input
                        type="text"
                        value={question}
                        onChange={(e) => setQuestion(e.target.value)}
                        placeholder="What would you like to know?"
                        required
                    />
                    <button type="submit" disabled={loading || !question.trim()}>
                        {loading ? '🔍 Searching...' : '🔍 Ask'}
                    </button>
                </div>
            </form>

            {error && <div className="error-message">{error}</div>}

            {answer && (
                <div className="answer-section">
                    <div className="answer-box">
                        <h3>Answer</h3>
                        <p>{answer.answer}</p>
                    </div>

                    {answer.sources && answer.sources.length > 0 && (
                        <div className="sources-section">
                            <h3>Sources ({answer.sources.length})</h3>
                            <div className="sources-grid">
                                {answer.sources.map((source, index) => (
                                    <SourceSnippet key={index} source={source} />
                                ))}
                            </div>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}

export default QueryInterface;
