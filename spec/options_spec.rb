require 'dev_dock/options'

RSpec.describe DevDock::Options do
  it 'forces a subcommand' do
    options = DevDock::Options::new [
      '-v', '/foo:/bar',
      'image'
    ]
    options.parse
    expect(options.error).not_to be_empty
  end
  it 'parses start subcommand' do
    options = DevDock::Options::new [
      'start',
      'image'
    ]
    options.parse
    expect(options.subcommand).to eq('start')
  end

  it 'parses volume options' do
    options = DevDock::Options::new [
      'start',
      '-v', 'foo:bar',
      'image'
    ]
    options.parse
    expect(options.volumes).to eq(['foo:bar'])
  end

  it 'doesnt allow invalid options' do
    options = DevDock::Options::new [
      'start',
      '--foobar',
      'image'
    ]
    options.parse
    expect(options.error).to_not be_empty
  end

  it 'parses the image image' do
    options = DevDock::Options::new [
      'start',
      'image'
    ]
    options.parse
    expect(options.image_name).to eql('image')
  end

  it 'allows you to specify environment' do
    options = DevDock::Options::new [
      'start', '-e', 'JIRA_USERNAME', 'image'
    ]
    options.parse
    expect(options.error).to be_nil
    expect(options.environment).to eql(['JIRA_USERNAME'])
  end

  it 'prevents from ommitting the environment variable itself' do
    options = DevDock::Options::new ['start', '-e', 'image']
    options.parse
    expect(options.error.nil?).to eql(false)
  end

  it 'allows to specify the command to start the container' do
    options = DevDock::Options::new ['start', 'image', 'screen']
    options.parse
    expect(options.run_command)
  end

end
