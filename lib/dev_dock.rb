require "dev_dock/container"
require "dev_dock/log"

module DevDock

  def self.start(options)
    container = DevDock::DevContainer.new(options)

    if not container.image.exist?
      Log::info('image does not exist, pulling')
      container.image.pull
    end

    container.volumes.create
    container.binds.create

    container.run
  end

  def self.purge(options)
    container = DevDock::DevContainer.new(options)
    if container.exist?
      container.kill
    end
    container.volumes.remove
  end

end
