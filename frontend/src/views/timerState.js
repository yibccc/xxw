export function getCountdownLabel(timer, now) {
  if (timer.status !== 'enabled') {
    return '已停止调度'
  }

  if (!timer.next_fire_at) {
    return '待计算'
  }

  const diff = new Date(timer.next_fire_at).getTime() - now
  if (diff <= 0) {
    return '即将触发'
  }

  const totalSeconds = Math.floor(diff / 1000)
  const hours = Math.floor(totalSeconds / 3600)
  const minutes = Math.floor((totalSeconds % 3600) / 60)
  const seconds = totalSeconds % 60

  if (hours > 0) return `${hours}小时 ${minutes}分 ${seconds}秒`
  if (minutes > 0) return `${minutes}分 ${seconds}秒`
  return `${seconds}秒`
}

export function getExpiredEnabledTimerIds(timers, now) {
  return timers
    .filter((timer) => timer.status === 'enabled' && timer.next_fire_at)
    .filter((timer) => new Date(timer.next_fire_at).getTime() <= now)
    .map((timer) => timer.id)
}
