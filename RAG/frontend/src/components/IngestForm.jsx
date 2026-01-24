import { useState } from 'react';
import './IngestForm.css';

function IngestForm({ onIngestSuccess }) {
    const [sourceType, setSourceType] = useState('note');
    const [content, setContent] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [success, setSuccess] = useState('');

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        setSuccess('');
        setLoading(true);

        try {
            const { ingestContent } = await import('../services/api');
            const result = await ingestContent(content, sourceType);
            setSuccess(result.message);
            setContent('');
            if (onIngestSuccess) onIngestSuccess();
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="ingest-form">
            <h2>Add to Knowledge Base</h2>

            <div className="source-type-toggle">
                <button
                    className={sourceType === 'note' ? 'active' : ''}
                    onClick={() => setSourceType('note')}
                    type="button"
                >
                    📝 Note
                </button>
                <button
                    className={sourceType === 'url' ? 'active' : ''}
                    onClick={() => setSourceType('url')}
                    type="button"
                >
                    🔗 URL
                </button>
            </div>

            <form onSubmit={handleSubmit}>
                {sourceType === 'note' ? (
                    <textarea
                        value={content}
                        onChange={(e) => setContent(e.target.value)}
                        placeholder="Enter your note here..."
                        rows="6"
                        required
                    />
                ) : (
                    <input
                        type="url"
                        value={content}
                        onChange={(e) => setContent(e.target.value)}
                        placeholder="https://example.com/article"
                        required
                    />
                )}

                <button type="submit" disabled={loading || !content.trim()}>
                    {loading ? 'Processing...' : `Add ${sourceType === 'note' ? 'Note' : 'URL'}`}
                </button>
            </form>

            {error && <div className="message error">{error}</div>}
            {success && <div className="message success">{success}</div>}
        </div>
    );
}

export default IngestForm;
