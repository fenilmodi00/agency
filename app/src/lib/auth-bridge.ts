import { account } from './appwrite';

export async function createAppwriteSession(clerkToken: string) {
  const response = await fetch('/api/auth/appwrite-session', {
    headers: {
      Authorization: `Bearer ${clerkToken}`,
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ message: 'Bridge failed' }));
    throw new Error(error.message || 'Failed to create Appwrite session');
  }

  const { userId, secret } = await response.json();
  await account.createSession({ userId, secret });

  return { userId, secret };
}
