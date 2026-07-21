// Twin of app/schemas/message.py (MessageRead).
export interface Message {
  id: number;
  body: string;
  created_at: string; // ISO timestamp
}