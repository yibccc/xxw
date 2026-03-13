import test from 'node:test'
import assert from 'node:assert/strict'

import { getCountdownLabel, getExpiredEnabledTimerIds } from './timerState.js'

test('已完成定时器显示已停止调度', () => {
  const label = getCountdownLabel(
    {
      id: 1,
      status: 'completed',
      next_fire_at: '2026-03-13T02:00:00.000Z',
    },
    Date.parse('2026-03-13T01:59:59.000Z'),
  )

  assert.equal(label, '已停止调度')
})

test('已到触发时间的启用定时器会被标记为需要刷新', () => {
  const expiredIds = getExpiredEnabledTimerIds(
    [
      {
        id: 1,
        status: 'enabled',
        next_fire_at: '2026-03-13T02:00:00.000Z',
      },
      {
        id: 2,
        status: 'enabled',
        next_fire_at: '2026-03-13T02:00:02.000Z',
      },
      {
        id: 3,
        status: 'completed',
        next_fire_at: '2026-03-13T01:59:50.000Z',
      },
    ],
    Date.parse('2026-03-13T02:00:00.000Z'),
  )

  assert.deepEqual(expiredIds, [1])
})
