import { streamRunEvents } from './api';

function sseResponse(text: string) {
  const encoder = new TextEncoder();
  return new Response(
    new ReadableStream({
      start(controller) {
        controller.enqueue(encoder.encode(text));
        controller.close();
      },
    }),
    { status: 200, headers: { 'Content-Type': 'text/event-stream' } },
  );
}

it('resumes with Last-Event-ID and ignores replayed event sequences', async () => {
  const fetchMock = vi
    .fn()
    .mockResolvedValueOnce(sseResponse(
      'id: 3\nevent: message.delta\ndata: {"delta":"已"}\n\n' +
      'id: 4\nevent: message.completed\ndata: {"content":"已完成"}\n\n',
    ))
    .mockResolvedValueOnce(sseResponse(
      'id: 4\nevent: message.completed\ndata: {"content":"已完成"}\n\n' +
      'id: 5\nevent: tool.completed\ndata: {"tool":"create_todo"}\n\n',
    ));
  vi.stubGlobal('fetch', fetchMock);
  const received: number[] = [];

  const cursor = await streamRunEvents('r1', 2, (event) => received.push(event.sequence));
  await streamRunEvents('r1', cursor, (event) => received.push(event.sequence));

  expect(received).toEqual([3, 4, 5]);
  expect(new Headers(fetchMock.mock.calls[1][1]?.headers).get('Last-Event-ID')).toBe('4');
});
