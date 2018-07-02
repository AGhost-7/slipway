require 'dev_dock/options'

RSpec.describe DevDock do
  it "forces a subcommand" do
    options = DevDock::Options::new [
      '-v', '/foo:/bar'
    ]
    assert(options.error)
  end
end
