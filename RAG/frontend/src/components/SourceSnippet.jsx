import './SourceSnippet.css';

function SourceSnippet({ source }) {
    const getRelevanceColor = (score) => {
        if (score >= 0.8) return '#48bb78';
        if (score >= 0.6) return '#ed8936';
        return '#a0aec0';
    };

    return (
        <div className="source-snippet">
            <div className="source-header">
                <span className="source-type">
                    {source.source_type === 'note' ? '📝 Note' : '🔗 URL'}
                </span>
                <span
                    className="relevance-badge"
                    style={{ backgroundColor: getRelevanceColor(source.relevance_score) }}
                >
                    {(source.relevance_score * 100).toFixed(0)}% match
                </span>
            </div>

            {source.url && (
                <div className="source-url">
                    <a href={source.url} target="_blank" rel="noopener noreferrer">
                        {source.url}
                    </a>
                </div>
            )}

            <div className="source-content">
                {source.content}
            </div>
        </div>
    );
}

export default SourceSnippet;
