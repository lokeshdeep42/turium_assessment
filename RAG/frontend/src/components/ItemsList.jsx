import { useState, useEffect } from 'react';
import './ItemsList.css';

function ItemsList({ refreshTrigger }) {
    const [items, setItems] = useState([]);
    const [filter, setFilter] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [expandedItems, setExpandedItems] = useState(new Set());
    const [deleteConfirm, setDeleteConfirm] = useState(null);

    const fetchItems = async () => {
        setLoading(true);
        setError('');
        try {
            const { getItems } = await import('../services/api');
            const data = await getItems(filter);
            setItems(data);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchItems();
    }, [filter, refreshTrigger]);

    const formatDate = (dateString) => {
        const date = new Date(dateString);
        return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], {
            hour: '2-digit',
            minute: '2-digit'
        });
    };

    const toggleExpand = (itemId) => {
        const newExpanded = new Set(expandedItems);
        if (newExpanded.has(itemId)) {
            newExpanded.delete(itemId);
        } else {
            newExpanded.add(itemId);
        }
        setExpandedItems(newExpanded);
    };

    const handleDeleteClick = (itemId) => {
        setDeleteConfirm(itemId);
    };

    const handleDeleteConfirm = async (itemId) => {
        try {
            const { deleteItem } = await import('../services/api');
            await deleteItem(itemId);
            setDeleteConfirm(null);
            fetchItems(); // Refresh the list
        } catch (err) {
            setError(`Failed to delete item: ${err.message}`);
            setDeleteConfirm(null);
        }
    };

    const handleDeleteCancel = () => {
        setDeleteConfirm(null);
    };

    return (
        <div className="items-list">
            <div className="items-header">
                <h2>Saved Items ({items.length})</h2>
                <div className="filter-buttons">
                    <button
                        className={filter === null ? 'active' : ''}
                        onClick={() => setFilter(null)}
                    >
                        All
                    </button>
                    <button
                        className={filter === 'note' ? 'active' : ''}
                        onClick={() => setFilter('note')}
                    >
                        Notes
                    </button>
                    <button
                        className={filter === 'url' ? 'active' : ''}
                        onClick={() => setFilter('url')}
                    >
                        URLs
                    </button>
                </div>
            </div>

            {loading && <div className="loading">Loading items...</div>}
            {error && <div className="error">{error}</div>}

            {!loading && items.length === 0 && (
                <div className="empty-state">
                    <p>No items yet. Add a note or URL to get started!</p>
                </div>
            )}

            <div className="items-grid">
                {items.map((item) => (
                    <div key={item.id} className={`item-card ${item.source_type}`}>
                        <div className="item-header">
                            <span className="item-type">
                                {item.source_type === 'note' ? '📝' : '🔗'} {item.source_type}
                            </span>
                            <span className="item-date">{formatDate(item.created_at)}</span>
                        </div>

                        {item.url && (
                            <div className="item-url">
                                <a href={item.url} target="_blank" rel="noopener noreferrer">
                                    {item.url}
                                </a>
                            </div>
                        )}

                        <div className="item-content">
                            {expandedItems.has(item.id)
                                ? item.content
                                : (item.content.length > 200
                                    ? item.content.substring(0, 200) + '...'
                                    : item.content)
                            }
                        </div>

                        <div className="item-actions">
                            {item.content.length > 200 && (
                                <button
                                    className="action-btn view-btn"
                                    onClick={() => toggleExpand(item.id)}
                                >
                                    {expandedItems.has(item.id) ? '📖 Show Less' : '📖 View Full'}
                                </button>
                            )}
                            <button
                                className="action-btn delete-btn"
                                onClick={() => handleDeleteClick(item.id)}
                            >
                                🗑️ Delete
                            </button>
                        </div>

                        {deleteConfirm === item.id && (
                            <div className="delete-confirm">
                                <p>Are you sure you want to delete this item?</p>
                                <div className="confirm-buttons">
                                    <button
                                        className="confirm-yes"
                                        onClick={() => handleDeleteConfirm(item.id)}
                                    >
                                        Yes, Delete
                                    </button>
                                    <button
                                        className="confirm-no"
                                        onClick={handleDeleteCancel}
                                    >
                                        Cancel
                                    </button>
                                </div>
                            </div>
                        )}
                    </div>
                ))}
            </div>
        </div>
    );
}

export default ItemsList;
