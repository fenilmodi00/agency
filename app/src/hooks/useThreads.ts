import { useState, useEffect, useCallback } from 'react';
import { tablesDB } from '@/lib/appwrite';
import { Query, Channel } from 'appwrite';
import { DATABASE_ID, TABLES } from '@/lib/constants';
import type { DealThread, Message } from '@/lib/types';
import { useRealtimeSubscription } from '@/lib/realtime';

const TEST_USER_ID = 'test-user-id';

interface ThreadWithPreview extends DealThread {
  lastMessagePreview: string;
}

interface UseThreadsResult {
  threads: ThreadWithPreview[];
  loading: boolean;
  error: string | null;
  refresh: () => Promise<void>;
}

export function useThreads(): UseThreadsResult {
  const [threads, setThreads] = useState<ThreadWithPreview[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchThreads = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const creatorsResult = await tablesDB.listRows({
        databaseId: DATABASE_ID,
        tableId: TABLES.CREATORS,
        queries: [Query.equal('clerk_user_id', TEST_USER_ID), Query.limit(1)],
      });

      if (creatorsResult.rows.length === 0) {
        setThreads([]);
        setLoading(false);
        return;
      }

      const creatorRow = creatorsResult.rows[0];
      const igUserId = creatorRow.ig_user_id as string;

      if (!igUserId) {
        setThreads([]);
        setLoading(false);
        return;
      }

      // Step 2: Fetch deal_threads for this ig_user_id
      const threadsResult = await tablesDB.listRows({
        databaseId: DATABASE_ID,
        tableId: TABLES.DEAL_THREADS,
        queries: [
          Query.equal('ig_user_id', igUserId),
          Query.orderDesc('last_message_at'),
        ],
      });

      const rawThreads = threadsResult.rows as unknown as DealThread[];

      // Step 3: Fetch last message preview for each thread
      const threadsWithPreviews = await Promise.all(
        rawThreads.map(async (thread) => {
          try {
            const messagesResult = await tablesDB.listRows({
              databaseId: DATABASE_ID,
              tableId: TABLES.MESSAGES,
              queries: [
                Query.equal('thread_id', thread.$id ?? ''),
                Query.orderDesc('timestamp'),
                Query.limit(1),
              ],
            });

            const lastMsg = messagesResult.rows[0] as unknown as Message | undefined;
            return {
              ...thread,
              lastMessagePreview: lastMsg?.body ?? '',
            };
          } catch {
            return {
              ...thread,
              lastMessagePreview: '',
            };
          }
        })
      );

      setThreads(threadsWithPreviews);
    } catch (err: unknown) {
      const apiErr = err as { message?: string };
      setError(apiErr.message ?? 'Failed to load threads');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchThreads();
  }, [fetchThreads]);

  const dealThreadsChannel = Channel.tablesdb(DATABASE_ID).table(TABLES.DEAL_THREADS).row();
  useRealtimeSubscription(dealThreadsChannel.toString(), () => {
    fetchThreads();
  });

  return { threads, loading, error, refresh: fetchThreads };
}
