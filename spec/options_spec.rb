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

end
