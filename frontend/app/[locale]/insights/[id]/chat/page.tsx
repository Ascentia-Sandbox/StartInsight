'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Loader2, MessageCircle, MessageSquare, Send, ArrowLeft, Sparkles,
  Target, Rocket, DollarSign, Shield, Plus, Trash2,
} from 'lucide-react';
import Link from 'next/link';
import { getSupabaseClient } from '@/lib/supabase/client';
import { fetchInsightById } from '@/lib/api';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Textarea } from '@/components/ui/textarea';
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from '@/components/ui/select';
import { config } from '@/lib/env';
import axios from 'axios';

const API_URL = config.apiUrl;

function createClient(token: string) {
  return axios.create({
    baseURL: API_URL,
    headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
  });
}

interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  created_at: string;
}

interface ChatSession {
  id: string;
  insight_id: string;
  title: string | null;
  mode: string | null;
  message_count: number;
  total_tokens: number;
  created_at: string;
  updated_at: string;
  messages: ChatMessage[];
}

interface ChatListItem {
  id: string;
  insight_id: string;
  title: string | null;
  mode: string | null;
  message_count: number;
  updated_at: string;
}

const MODE_CONFIG = {
  general: {
    label: 'General',
    description: 'Open-ended strategy discussion',
    icon: MessageSquare,
    color: 'text-purple-600',
    bg: 'bg-purple-50 dark:bg-purple-950/30',
  },
  pressure_test: {
    label: 'Pressure Test',
    description: 'Challenge assumptions with hard questions',
    icon: Shield,
    color: 'text-red-600',
    bg: 'bg-red-50 dark:bg-red-950/30',
  },
  gtm_planning: {
    label: 'GTM Planning',
    description: 'Go-to-market strategy, channels, pricing',
    icon: Rocket,
    color: 'text-blue-600',
    bg: 'bg-blue-50 dark:bg-blue-950/30',
  },
  pricing_strategy: {
    label: 'Pricing Strategy',
    description: 'Get pricing and monetization advice',
    icon: DollarSign,
    color: 'text-green-600',
    bg: 'bg-green-50 dark:bg-green-950/30',
  },
  competitive: {
    label: 'Competitive',
    description: 'Competitive landscape analysis',
    icon: Target,
    color: 'text-amber-600',
    bg: 'bg-amber-50 dark:bg-amber-950/30',
  },
} as const;

type ChatMode = keyof typeof MODE_CONFIG;

export default function ChatPage() {
  const params = useParams();
  const router = useRouter();
  const queryClient = useQueryClient();
  const insightId = params.id as string;

  const [accessToken, setAccessToken] = useState<string | null>(null);
  const [activeChatId, setActiveChatId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [selectedMode, setSelectedMode] = useState<ChatMode>('general');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auth
  useEffect(() => {
    const supabase = getSupabaseClient();
    supabase.auth.getSession().then(({ data }: { data: { session: { access_token: string } | null } }) => {
      if (data.session?.access_token) setAccessToken(data.session.access_token);
      else router.push(`/auth/login?redirectTo=/insights/${insightId}/chat`);
    });
  }, [router, insightId]);

  // Fetch insight details
  const { data: insight } = useQuery({
    queryKey: ['insight', insightId],
    queryFn: () => fetchInsightById(insightId),
    enabled: !!insightId,
  });

  // Fetch chat sessions for this insight
  const { data: chatSessions, isLoading: sessionsLoading } = useQuery({
    queryKey: ['chat-sessions', insightId, accessToken],
    queryFn: async () => {
      const client = createClient(accessToken!);
      const { data } = await client.get('/api/idea-chats', {
        params: { insight_id: insightId, limit: 50 },
      });
      return data as { items: ChatListItem[]; total: number };
    },
    enabled: !!accessToken,
  });

  // Fetch active chat messages
  const { data: activeChat } = useQuery({
    queryKey: ['chat-detail', activeChatId, accessToken],
    queryFn: async () => {
      const client = createClient(accessToken!);
      const { data } = await client.get(`/api/idea-chats/${activeChatId}`);
      return data as ChatSession;
    },
    enabled: !!activeChatId && !!accessToken,
  });

  // When active chat loads, update messages
  useEffect(() => {
    if (activeChat?.messages) {
      setMessages(activeChat.messages);
    }
  }, [activeChat]);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Create new chat session
  const createChatMutation = useMutation({
    mutationFn: async (mode: ChatMode) => {
      const client = createClient(accessToken!);
      const { data } = await client.post('/api/idea-chats', {
        insight_id: insightId,
        mode,
      });
      return data as ChatSession;
    },
    onSuccess: (data) => {
      setActiveChatId(data.id);
      setMessages([]);
      queryClient.invalidateQueries({ queryKey: ['chat-sessions'] });
    },
  });

  // Delete chat session
  const deleteChatMutation = useMutation({
    mutationFn: async (chatId: string) => {
      const client = createClient(accessToken!);
      await client.delete(`/api/idea-chats/${chatId}`);
    },
    onSuccess: (_, chatId) => {
      if (activeChatId === chatId) {
        setActiveChatId(null);
        setMessages([]);
      }
      queryClient.invalidateQueries({ queryKey: ['chat-sessions'] });
    },
  });

  // Send message with SSE streaming
  const sendMessage = useCallback(async () => {
    if (!input.trim() || !activeChatId || !accessToken || isStreaming) return;

    const userMessage = input.trim();
    setInput('');
    setIsStreaming(true);

    // Optimistically add user message
    const tempUserMsg: ChatMessage = {
      id: `temp-${Date.now()}`,
      role: 'user',
      content: userMessage,
      created_at: new Date().toISOString(),
    };
    setMessages(prev => [...prev, tempUserMsg]);

    try {
      const response = await fetch(`${API_URL}/api/idea-chats/${activeChatId}/messages`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${accessToken}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ content: userMessage }),
      });

      if (!response.ok) throw new Error('Failed to send message');

      const reader = response.body?.getReader();
      if (!reader) throw new Error('No stream reader');

      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue;
          try {
            const event = JSON.parse(line.slice(6));
            if (event.type === 'user_message') {
              // Replace temp message with real one
              setMessages(prev =>
                prev.map(m => m.id === tempUserMsg.id
                  ? { ...m, id: event.id }
                  : m
                )
              );
            } else if (event.type === 'assistant_message') {
              setMessages(prev => [...prev, {
                id: event.id,
                role: 'assistant',
                content: event.content,
                created_at: new Date().toISOString(),
              }]);
            } else if (event.type === 'error') {
              setMessages(prev => [...prev, {
                id: `error-${Date.now()}`,
                role: 'assistant',
                content: `Error: ${event.message}`,
                created_at: new Date().toISOString(),
              }]);
            }
          } catch {
            // Ignore parse errors
          }
        }
      }

      queryClient.invalidateQueries({ queryKey: ['chat-sessions'] });
    } catch (err) {
      setMessages(prev => [...prev, {
        id: `error-${Date.now()}`,
        role: 'assistant',
        content: 'Failed to get response. Please try again.',
        created_at: new Date().toISOString(),
      }]);
    } finally {
      setIsStreaming(false);
    }
  }, [input, activeChatId, accessToken, isStreaming, queryClient]);

  // Handle Enter key
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  if (!accessToken) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-6 w-6 animate-spin" />
      </div>
    );
  }

  const activeModeConfig = activeChatId && activeChat?.mode
    ? MODE_CONFIG[activeChat.mode as ChatMode]
    : null;

  return (
    <div className="container mx-auto px-4 py-6 max-w-6xl">
      {/* Header */}
      <div className="flex items-center gap-3 mb-6">
        <Button asChild variant="ghost" size="icon">
          <Link href={`/insights/${insightId}`}>
            <ArrowLeft className="h-4 w-4" />
          </Link>
        </Button>
        <div className="flex-1">
          <h1 className="text-xl font-bold flex items-center gap-2">
            <MessageCircle className="h-5 w-5 text-purple-600" />
            AI Chat Strategist
          </h1>
          {insight && (
            <p className="text-sm text-muted-foreground truncate max-w-lg">
              {insight.proposed_solution}
            </p>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6" style={{ height: 'calc(100vh - 180px)' }}>
        {/* Sidebar: Chat Sessions */}
        <div className="lg:col-span-1 flex flex-col gap-3">
          {/* New Chat */}
          <Card>
            <CardContent className="p-4 space-y-3">
              <h3 className="text-sm font-semibold">New Chat</h3>
              <Select value={selectedMode} onValueChange={(v) => setSelectedMode(v as ChatMode)}>
                <SelectTrigger className="text-sm">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {(Object.entries(MODE_CONFIG) as [ChatMode, typeof MODE_CONFIG[ChatMode]][]).map(([key, cfg]) => (
                    <SelectItem key={key} value={key}>
                      <span className="flex items-center gap-2">
                        <cfg.icon className={`h-3 w-3 ${cfg.color}`} />
                        {cfg.label}
                      </span>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <Button
                className="w-full"
                size="sm"
                onClick={() => createChatMutation.mutate(selectedMode)}
                disabled={createChatMutation.isPending}
              >
                {createChatMutation.isPending ? (
                  <Loader2 className="h-3 w-3 mr-2 animate-spin" />
                ) : (
                  <Plus className="h-3 w-3 mr-2" />
                )}
                Start Session
              </Button>
            </CardContent>
          </Card>

          {/* Session List */}
          <div className="flex-1 overflow-y-auto space-y-1">
            {sessionsLoading ? (
              <div className="flex justify-center py-4">
                <Loader2 className="h-4 w-4 animate-spin" />
              </div>
            ) : (
              chatSessions?.items?.map((session) => {
                const cfg = session.mode ? MODE_CONFIG[session.mode as ChatMode] : null;
                return (
                  <div
                    key={session.id}
                    className={`p-3 rounded-lg cursor-pointer border transition-colors ${
                      activeChatId === session.id
                        ? 'border-purple-500 bg-purple-50 dark:bg-purple-950/30'
                        : 'border-transparent hover:bg-muted'
                    }`}
                    onClick={() => setActiveChatId(session.id)}
                  >
                    <div className="flex items-start justify-between gap-1">
                      <div className="flex-1 min-w-0">
                        {cfg && (
                          <Badge variant="outline" className={`text-[10px] mb-1 ${cfg.color}`}>
                            {cfg.label}
                          </Badge>
                        )}
                        <p className="text-xs text-muted-foreground truncate">
                          {session.message_count} messages
                        </p>
                      </div>
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-6 w-6 text-muted-foreground hover:text-destructive"
                        onClick={(e) => {
                          e.stopPropagation();
                          deleteChatMutation.mutate(session.id);
                        }}
                      >
                        <Trash2 className="h-3 w-3" />
                      </Button>
                    </div>
                  </div>
                );
              })
            )}
            {chatSessions && chatSessions.items.length === 0 && (
              <p className="text-xs text-muted-foreground text-center py-4">
                No chat sessions yet. Start one above.
              </p>
            )}
          </div>
        </div>

        {/* Main Chat Area */}
        <div className="lg:col-span-3 flex flex-col">
          {!activeChatId ? (
            /* Mode Selection Cards */
            <div className="flex-1 flex items-center justify-center">
              <div className="text-center space-y-6 max-w-lg">
                <Sparkles className="h-12 w-12 mx-auto text-purple-500 opacity-60" />
                <h2 className="text-xl font-semibold">Choose a Strategy Mode</h2>
                <p className="text-sm text-muted-foreground">
                  Select a mode and start a conversation with your AI strategist
                </p>
                <div className="grid gap-3">
                  {(Object.entries(MODE_CONFIG) as [ChatMode, typeof MODE_CONFIG[ChatMode]][]).map(([key, cfg]) => (
                    <button
                      key={key}
                      className={`flex items-center gap-4 p-4 rounded-lg border text-left transition-all hover:shadow-md ${cfg.bg}`}
                      onClick={() => createChatMutation.mutate(key)}
                      disabled={createChatMutation.isPending}
                    >
                      <cfg.icon className={`h-8 w-8 ${cfg.color}`} />
                      <div>
                        <div className="font-semibold">{cfg.label}</div>
                        <div className="text-sm text-muted-foreground">{cfg.description}</div>
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            /* Active Chat */
            <>
              {/* Mode selector row */}
              <div className="flex gap-2 p-4 border-b overflow-x-auto">
                {(Object.entries(MODE_CONFIG) as [ChatMode, typeof MODE_CONFIG[ChatMode]][]).map(([key, cfg]) => {
                  const isActive = activeChat?.mode === key;
                  return (
                    <button
                      key={key}
                      onClick={() => {
                        if (!isActive) {
                          // Start a new chat session with this mode
                          createChatMutation.mutate(key);
                        }
                      }}
                      className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium whitespace-nowrap transition-colors ${
                        isActive
                          ? 'bg-primary text-primary-foreground'
                          : 'bg-secondary text-secondary-foreground hover:bg-secondary/80'
                      }`}
                    >
                      <cfg.icon className="h-4 w-4" />
                      {cfg.label}
                    </button>
                  );
                })}
              </div>

              {/* Messages */}
              <div className="flex-1 overflow-y-auto p-4 space-y-4 border border-t-0 rounded-b-lg bg-background">
                {messages.length === 0 && (
                  <div className="text-center py-12 text-muted-foreground">
                    <MessageCircle className="h-8 w-8 mx-auto mb-3 opacity-40" />
                    <p className="text-sm">Start the conversation. Ask anything about this idea.</p>
                  </div>
                )}
                {messages.map((msg) => (
                  <div
                    key={msg.id}
                    className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                  >
                    <div
                      className={`max-w-[80%] rounded-2xl px-4 py-3 text-sm whitespace-pre-wrap ${
                        msg.role === 'user'
                          ? 'bg-purple-600 text-white rounded-br-md'
                          : 'bg-muted rounded-bl-md'
                      }`}
                    >
                      {msg.content}
                    </div>
                  </div>
                ))}
                {isStreaming && (
                  <div className="flex justify-start">
                    <div className="bg-muted rounded-2xl rounded-bl-md px-4 py-3">
                      <div className="flex items-center gap-2 text-sm text-muted-foreground">
                        <Loader2 className="h-3 w-3 animate-spin" />
                        Thinking...
                      </div>
                    </div>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </div>

              {/* Input */}
              <div className="mt-3 flex gap-2">
                <Textarea
                  ref={textareaRef}
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder="Ask about this idea..."
                  rows={1}
                  className="resize-none min-h-[44px] max-h-[120px]"
                  disabled={isStreaming}
                />
                <Button
                  onClick={sendMessage}
                  disabled={!input.trim() || isStreaming}
                  className="bg-purple-600 hover:bg-purple-700 self-end"
                  size="icon"
                >
                  {isStreaming ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Send className="h-4 w-4" />
                  )}
                </Button>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
