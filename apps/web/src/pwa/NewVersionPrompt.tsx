import { useRegisterSW } from './registerSW'

export function NewVersionPrompt() {
  const {
    needRefresh: [needRefresh, setNeedRefresh],
    updateServiceWorker,
  } = useRegisterSW({
    onRegisterError(err) {
      console.warn('[pwa] SW register failed', err)
    },
  })

  if (!needRefresh) return null
  return (
    <div className="pwa-toast" role="status">
      <span>A new version of SideQuest is available.</span>
      <button
        onClick={() => {
          void updateServiceWorker(true)
          setNeedRefresh(false)
        }}
      >
        Reload
      </button>
    </div>
  )
}
