
import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import {
    BrainCircuit,
    FileText,
    FolderPlus,
    Send,
    Upload,
} from "lucide-react";
import "./App.css";

const API_URL = "http://127.0.0.1:8000";

type Collection = {
    id: string;
    name: string;
    created_at: string;
};

type Document = {
    id: string;
    name: string;
    page_count: number;
    character_count: number;
    status: string;
};

type Source = {
    chunk_id: string;
    document_name: string;
    page_number: number;
    text: string;
    score: number;
};

type Message = {
    role: "user" | "assistant";
    content: string;
    sources?: Source[];
};

function App() {
    const [collections, setCollections] = useState<Collection[]>([]);
    const [activeCollection, setActiveCollection] =
        useState<Collection | null>(null);
    const [documents, setDocuments] = useState<Document[]>([]);
    const [messages, setMessages] = useState<Message[]>([]);
    const [collectionName, setCollectionName] = useState("");
    const [question, setQuestion] = useState("");
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");

    async function loadCollections() {
        const response = await fetch(`${API_URL}/collections`);
        const data = await response.json();

        setCollections(data);

        if (!activeCollection && data.length > 0) {
            setActiveCollection(data[0]);
        }
    }

    async function loadDocuments(collectionId: string) {
        const response = await fetch(
            `${API_URL}/collections/${collectionId}/documents`,
        );

        setDocuments(await response.json());
    }

    useEffect(() => {
        loadCollections().catch(() =>
            setError("Could not connect to the QueryMind API."),
        );
    }, []);

    useEffect(() => {
        if (activeCollection) {
            loadDocuments(activeCollection.id);
            setMessages([]);
        }
    }, [activeCollection]);

    async function createCollection(event: FormEvent) {
        event.preventDefault();

        if (!collectionName.trim()) {
            return;
        }

        const response = await fetch(`${API_URL}/collections`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                name: collectionName,
            }),
        });

        const collection = await response.json();

        setCollections((current) => [collection, ...current]);
        setActiveCollection(collection);
        setCollectionName("");
    }

    async function uploadDocument(file: File) {
        if (!activeCollection) {
            return;
        }

        setLoading(true);
        setError("");

        const formData = new FormData();
        formData.append("file", file);

        try {
            const response = await fetch(
                `${API_URL}/collections/${activeCollection.id}/documents`,
                {
                    method: "POST",
                    body: formData,
                },
            );

            if (!response.ok) {
                const result = await response.json();
                throw new Error(result.detail);
            }

            await loadDocuments(activeCollection.id);
        } catch (uploadError) {
            setError(
                uploadError instanceof Error
                    ? uploadError.message
                    : "Document upload failed.",
            );
        } finally {
            setLoading(false);
        }
    }

    async function askQuestion(event: FormEvent) {
        event.preventDefault();

        if (!activeCollection || !question.trim() || loading) {
            return;
        }

        const submittedQuestion = question;

        setQuestion("");
        setLoading(true);
        setError("");
        setMessages((current) => [
            ...current,
            {
                role: "user",
                content: submittedQuestion,
            },
        ]);

        try {
            const response = await fetch(`${API_URL}/chat`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({
                    collection_id: activeCollection.id,
                    question: submittedQuestion,
                    top_k: 3,
                }),
            });

            if (!response.ok) {
                const result = await response.json();
                throw new Error(result.detail);
            }

            const result = await response.json();

            setMessages((current) => [
                ...current,
                {
                    role: "assistant",
                    content: result.answer,
                    sources: result.sources,
                },
            ]);
        } catch (chatError) {
            setError(
                chatError instanceof Error
                    ? chatError.message
                    : "QueryMind could not answer the question.",
            );
        } finally {
            setLoading(false);
        }
    }
    return (
        <div className="app">
            <aside className="sidebar">
                <div className="brand">
                    <BrainCircuit />
                    <div>
                        <strong>QueryMind</strong>
                        <span>Document intelligence</span>
                    </div>
                </div>

                <form className="collection-form" onSubmit={createCollection}>
                    <input
                        value={collectionName}
                        onChange={(event) => setCollectionName(event.target.value)}
                        placeholder="New collection"
                    />
                    <button aria-label="Create collection">
                        <FolderPlus size={18} />
                    </button>
                </form>

                <p className="sidebar-label">COLLECTIONS</p>

                <nav className="collection-list">
                    {collections.map((collection) => (
                        <button
                            className={activeCollection?.id === collection.id ? "active" : ""}
                            key={collection.id}
                            onClick={() => setActiveCollection(collection)}
                        >
                            <FileText size={17} />
                            {collection.name}
                        </button>
                    ))}
                </nav>
            </aside>

            <main>
                <header className="header">
                    <div>
                        <span>COLLECTION</span>
                        <h1>{activeCollection?.name ?? "No collection selected"}</h1>
                    </div>
                    <div className="status">
                        <i />
                        Local RAG ready
                    </div>
                </header>

                {error && <div className="error">{error}</div>}

                <div className="workspace">
                    <section className="chat">
                        <div className="section-heading">
                            <h2>Ask your documents</h2>
                            <p>Answers are grounded in retrieved sources.</p>
                        </div>

                        <div className="messages">
                            {messages.length === 0 ? (
                                <div className="empty">
                                    <BrainCircuit size={38} />
                                    <h2>What do you want to know?</h2>
                                    <p>Upload documents and ask a question about their contents.</p>
                                </div>
                            ) : (
                                messages.map((message, index) => (
                                    <article className={message.role} key={index}>
                                        <label>{message.role === "user" ? "YOU" : "QUERYMIND"}</label>
                                        <div className="bubble">{message.content}</div>

                                        {message.sources && message.sources.length > 0 && (
                                            <div className="sources">
                                                <strong>Sources</strong>
                                                {message.sources.map((source, sourceIndex) => (
                                                    <details key={source.chunk_id}>
                                                        <summary>
                                                            [{sourceIndex + 1}] {source.document_name} — page {source.page_number}
                                                            <span>{Math.round(source.score * 100)}% match</span>
                                                        </summary>
                                                        <p>{source.text}</p>
                                                    </details>
                                                ))}
                                            </div>
                                        )}
                                    </article>
                                ))
                            )}

                            {loading && <div className="loading">QueryMind is thinking…</div>}
                        </div>

                        <form className="composer" onSubmit={askQuestion}>
                            <textarea
                                value={question}
                                onChange={(event) => setQuestion(event.target.value)}
                                placeholder="Ask a question about your documents..."
                            />
                            <button disabled={!question.trim() || loading}>
                                <Send size={19} />
                            </button>
                        </form>
                    </section>

                    <aside className="documents-panel">
                        <div className="section-heading">
                            <h2>Documents</h2>
                            <p>{documents.length} indexed</p>
                        </div>

                        <label className="upload">
                            <Upload />
                            <strong>{loading ? "Processing…" : "Upload a document"}</strong>
                            <span>PDF, DOCX, TXT or Markdown</span>
                            <input
                                type="file"
                                accept=".pdf,.docx,.txt,.md"
                                disabled={!activeCollection || loading}
                                onChange={(event) => {
                                    const file = event.target.files?.[0];
                                    if (file) uploadDocument(file);
                                }}
                            />
                        </label>

                        <div className="document-list">
                            {documents.map((document) => (
                                <div className="document" key={document.id}>
                                    <FileText size={18} />
                                    <div>
                                        <strong>{document.name}</strong>
                                        <span>{document.page_count} pages · {document.status}</span>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </aside>
                </div>
            </main>
        </div>
    );
}

export default App;
